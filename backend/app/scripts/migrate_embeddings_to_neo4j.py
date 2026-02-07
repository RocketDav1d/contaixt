"""
Migration script: Copy embeddings from pgvector to Neo4j.

This script reads all document chunks with embeddings from PostgreSQL
and creates corresponding Chunk nodes in Neo4j with their embeddings.

Run via: python -m app.scripts.migrate_embeddings_to_neo4j

The script is idempotent - it uses MERGE to avoid duplicates.

Uses singleton driver from neo4j_client for connection pooling.
Reference: https://neo4j.com/blog/developer/neo4j-driver-best-practices/
"""

import asyncio
import logging

from sqlalchemy import func, select

from app.db import get_async_session
from app.models import Document, DocumentChunk
from app.neo4j_client import get_session, verify_connectivity, close_driver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BATCH_SIZE = 100  # Process chunks in batches for memory efficiency


async def migrate_embeddings() -> None:
    """Migrate all embeddings from pgvector to Neo4j."""
    Session = get_async_session()

    # Verify Neo4j connectivity first
    if not await verify_connectivity():
        logger.error("Cannot connect to Neo4j. Aborting migration.")
        return

    # First, get all documents with their source_connection_id
    async with Session() as session:
        result = await session.execute(
            select(Document.id, Document.workspace_id, Document.source_connection_id)
        )
        docs = {
            str(row[0]): {"workspace_id": str(row[1]), "source_connection_id": str(row[2])}
            for row in result.fetchall()
        }

    logger.info("Found %d documents", len(docs))

    # Get total count of chunks with embeddings
    async with Session() as session:
        result = await session.execute(
            select(func.count()).select_from(DocumentChunk).where(DocumentChunk.embedding.isnot(None))
        )
        total_chunks = result.scalar_one()

    logger.info("Found %d chunks with embeddings to migrate", total_chunks)

    if total_chunks == 0:
        logger.info("No embeddings to migrate")
        return

    migrated = 0
    offset = 0

    while offset < total_chunks:
        # Fetch batch of chunks from PostgreSQL
        async with Session() as session:
            result = await session.execute(
                select(DocumentChunk)
                .where(DocumentChunk.embedding.isnot(None))
                .order_by(DocumentChunk.id)
                .offset(offset)
                .limit(BATCH_SIZE)
            )
            chunks = list(result.scalars().all())

        if not chunks:
            break

        # Group chunks by document for efficient batching
        chunks_by_doc: dict[str, list] = {}
        for chunk in chunks:
            doc_id = str(chunk.document_id)
            if doc_id not in chunks_by_doc:
                chunks_by_doc[doc_id] = []
            chunks_by_doc[doc_id].append(chunk)

        # Process each document's chunks using the singleton session
        async with get_session() as neo_session:
            for doc_id, doc_chunks in chunks_by_doc.items():
                doc_info = docs.get(doc_id)
                if not doc_info:
                    logger.warning("Document not found: %s", doc_id)
                    continue

                ws = doc_info["workspace_id"]
                conn_id = doc_info["source_connection_id"]

                # Ensure Document node exists
                await neo_session.run(
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

                # Prepare chunk data
                chunk_data = [
                    {
                        "chunk_id": str(c.id),
                        "idx": c.idx,
                        "text": c.text,
                        "start_offset": c.start_offset,
                        "end_offset": c.end_offset,
                        "embedding": list(c.embedding) if c.embedding is not None else None,
                    }
                    for c in doc_chunks
                ]

                # Batch upsert chunks
                await neo_session.run(
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

                migrated += len(doc_chunks)

        offset += BATCH_SIZE
        logger.info("Migrated %d/%d chunks (%.1f%%)", migrated, total_chunks, 100 * migrated / total_chunks)

    logger.info("Migration complete: %d chunks migrated to Neo4j", migrated)


async def verify_migration() -> None:
    """Verify the migration by comparing counts."""
    Session = get_async_session()

    # Count in PostgreSQL
    async with Session() as session:
        result = await session.execute(
            select(func.count()).select_from(DocumentChunk).where(DocumentChunk.embedding.isnot(None))
        )
        pg_count = result.scalar_one()

    # Count in Neo4j using the singleton session
    async with get_session() as session:
        result = await session.run("MATCH (c:Chunk) WHERE c.embedding IS NOT NULL RETURN count(c) AS count")
        record = await result.single()
        neo4j_count = record["count"] if record else 0

    logger.info("PostgreSQL chunks with embeddings: %d", pg_count)
    logger.info("Neo4j Chunk nodes with embeddings: %d", neo4j_count)

    if pg_count == neo4j_count:
        logger.info("✓ Migration verified: counts match")
    else:
        logger.warning("⚠ Count mismatch: PostgreSQL=%d, Neo4j=%d", pg_count, neo4j_count)


async def main() -> None:
    """Run migration and verification, then clean up."""
    try:
        await migrate_embeddings()
        await verify_migration()
    finally:
        await close_driver()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
