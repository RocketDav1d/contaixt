"""
OpenAI embeddings writer.

Embeds chunk texts and stores vectors in:
- Neo4j as Chunk nodes with vector embeddings (primary - for unified vector+graph queries)
- PostgreSQL pgvector column (legacy - kept for backward compatibility during migration)

The Neo4j Chunk nodes enable unified Cypher queries that combine vector search
with graph traversal in a single query.
"""

import logging
import uuid

from openai import AsyncOpenAI
from sqlalchemy import select, update

from app.config import settings
from app.db import get_async_session
from app.models import Document, DocumentChunk
from app.neo4j_client import get_session

logger = logging.getLogger(__name__)

MODEL = "text-embedding-3-small"
BATCH_SIZE = 50  # OpenAI allows up to 2048 inputs, but keep batches manageable


async def _upsert_chunks_to_neo4j(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    source_connection_id: uuid.UUID,
    chunks_with_embeddings: list[tuple[DocumentChunk, list[float]]],
) -> None:
    """
    Upsert Chunk nodes to Neo4j with embeddings.

    Creates:
    - Document node (MERGE, idempotent) with source_connection_id for vault filtering
    - Chunk nodes with embedding vectors and source_connection_id
    - PART_OF relationships from Chunk to Document

    source_connection_id is stored on both Document and Chunk nodes for efficient
    vault filtering (Chunk nodes can be filtered directly without traversal).

    Uses the singleton driver from neo4j_client for connection pooling.
    """
    if not chunks_with_embeddings:
        return

    ws = str(workspace_id)
    doc_id = str(document_id)
    conn_id = str(source_connection_id)

    async with get_session() as session:
        # Ensure Document node exists with source_connection_id (idempotent MERGE)
        await session.run(
            """
            MERGE (d:Document {workspace_id: $ws, key: $key})
            SET d.document_id = $doc_id,
                d.source_connection_id = $conn_id
            """,
            ws=ws,
            key=f"doc:{doc_id}",
            doc_id=doc_id,
            conn_id=conn_id,
        )

        # Batch upsert chunks with embeddings
        # Using UNWIND for efficient batch processing
        # source_connection_id on Chunk enables direct vault filtering without traversal
        chunk_data = [
            {
                "chunk_id": str(chunk.id),
                "idx": chunk.idx,
                "text": chunk.text,
                "start_offset": chunk.start_offset,
                "end_offset": chunk.end_offset,
                "embedding": embedding,
            }
            for chunk, embedding in chunks_with_embeddings
        ]

        await session.run(
            """
            UNWIND $chunks AS c
            MERGE (chunk:Chunk {
                workspace_id: $ws,
                document_id: $doc_id,
                idx: c.idx
            })
            SET chunk.chunk_id = c.chunk_id,
                chunk.text = c.text,
                chunk.start_offset = c.start_offset,
                chunk.end_offset = c.end_offset,
                chunk.embedding = c.embedding,
                chunk.source_connection_id = $conn_id

            WITH chunk
            MATCH (d:Document {workspace_id: $ws, key: $doc_key})
            MERGE (chunk)-[:PART_OF]->(d)
            """,
            ws=ws,
            doc_id=doc_id,
            doc_key=f"doc:{doc_id}",
            conn_id=conn_id,
            chunks=chunk_data,
        )

    logger.info("Upserted %d chunks to Neo4j for doc=%s", len(chunks_with_embeddings), doc_id)


async def embed_and_store(workspace_id: uuid.UUID, document_id: uuid.UUID) -> int:
    """
    Embed all chunks for a document and store vectors.

    Writes embeddings to:
    1. Neo4j Chunk nodes (for unified vector+graph queries)
    2. PostgreSQL pgvector column (legacy, for backward compatibility)

    Returns count of chunks embedded.
    """
    Session = get_async_session()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Fetch document to get source_connection_id for vault filtering in Neo4j
    async with Session() as session:
        doc_result = await session.execute(
            select(Document.source_connection_id).where(
                Document.id == document_id,
                Document.workspace_id == workspace_id,
            )
        )
        doc_row = doc_result.one_or_none()

    if not doc_row:
        logger.warning("Document not found: %s", document_id)
        return 0

    source_connection_id = doc_row[0]

    async with Session() as session:
        result = await session.execute(
            select(DocumentChunk)
            .where(
                DocumentChunk.workspace_id == workspace_id,
                DocumentChunk.document_id == document_id,
                DocumentChunk.embedding.is_(None),
            )
            .order_by(DocumentChunk.idx)
        )
        chunks = list(result.scalars().all())

    if not chunks:
        return 0

    embedded = 0
    all_chunks_with_embeddings: list[tuple[DocumentChunk, list[float]]] = []

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c.text for c in batch]

        resp = await client.embeddings.create(input=texts, model=MODEL)

        # Collect chunks with their embeddings for Neo4j batch upsert
        batch_with_embeddings = [
            (chunk, emb_data.embedding)
            for chunk, emb_data in zip(batch, resp.data, strict=True)
        ]
        all_chunks_with_embeddings.extend(batch_with_embeddings)

        # Write to PostgreSQL pgvector (legacy)
        async with Session() as session:
            for chunk, embedding in batch_with_embeddings:
                await session.execute(
                    update(DocumentChunk)
                    .where(DocumentChunk.id == chunk.id)
                    .values(embedding=embedding)
                )
            await session.commit()

        embedded += len(batch)
        logger.info("Embedded batch %d-%d for doc=%s", i, i + len(batch), document_id)

    # Write all chunks to Neo4j in one batch
    await _upsert_chunks_to_neo4j(
        workspace_id, document_id, source_connection_id, all_chunks_with_embeddings
    )

    return embedded
