"""
Context builder for GraphRAG queries.

1. Embed prompt → pgvector top-k chunk search
2. Seed entities from entity_mentions for those chunks
3. Neo4j traversal from seed entities up to `depth`
4. Return chunks + graph facts for the answer composer
"""

import logging
import uuid

from neo4j import AsyncGraphDatabase
from openai import AsyncOpenAI
from sqlalchemy import select, text

from app.config import settings
from app.db import get_async_session
from app.models import Document, DocumentChunk, EntityMention

logger = logging.getLogger(__name__)

EMBED_MODEL = "text-embedding-3-small"


async def embed_query(query: str) -> list[float]:
    """Embed a query string via OpenAI."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resp = await client.embeddings.create(input=[query], model=EMBED_MODEL)
    return resp.data[0].embedding


async def top_k_chunks(
    workspace_id: uuid.UUID,
    query_embedding: list[float],
    top_k: int = 20,
    vault_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    """Retrieve top-k similar chunks from pgvector, optionally filtered by vault_ids."""
    Session = get_async_session()
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    if vault_ids:
        sql = text("""
            SELECT
                dc.id, dc.document_id, dc.idx, dc.text,
                dc.start_offset, dc.end_offset,
                dc.embedding <=> :embedding AS distance
            FROM document_chunks dc
            WHERE dc.workspace_id = :ws
              AND dc.vault_id = ANY(:vault_ids)
              AND dc.embedding IS NOT NULL
            ORDER BY dc.embedding <=> :embedding
            LIMIT :top_k
        """)
        params = {
            "ws": str(workspace_id),
            "embedding": embedding_str,
            "top_k": top_k,
            "vault_ids": [str(v) for v in vault_ids],
        }
    else:
        sql = text("""
            SELECT
                dc.id, dc.document_id, dc.idx, dc.text,
                dc.start_offset, dc.end_offset,
                dc.embedding <=> :embedding AS distance
            FROM document_chunks dc
            WHERE dc.workspace_id = :ws
              AND dc.embedding IS NOT NULL
            ORDER BY dc.embedding <=> :embedding
            LIMIT :top_k
        """)
        params = {"ws": str(workspace_id), "embedding": embedding_str, "top_k": top_k}

    async with Session() as session:
        result = await session.execute(sql, params)
        rows = result.fetchall()

    chunks = []
    for row in rows:
        chunks.append({
            "chunk_id": str(row.id),
            "document_id": str(row.document_id),
            "idx": row.idx,
            "text": row.text,
            "start_offset": row.start_offset,
            "end_offset": row.end_offset,
            "distance": row.distance,
        })

    return chunks


async def seed_entities(
    workspace_id: uuid.UUID,
    chunk_document_ids: list[uuid.UUID],
    vault_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    """Get entity keys mentioned in the given documents (from entity_mentions table)."""
    if not chunk_document_ids:
        return []

    Session = get_async_session()
    async with Session() as session:
        stmt = (
            select(
                EntityMention.entity_key,
                EntityMention.entity_type,
                EntityMention.entity_name,
            )
            .where(
                EntityMention.workspace_id == workspace_id,
                EntityMention.document_id.in_(chunk_document_ids),
            )
            .distinct(EntityMention.entity_key)
        )
        if vault_ids:
            stmt = stmt.where(EntityMention.vault_id.in_(vault_ids))

        result = await session.execute(stmt)
        rows = result.fetchall()

    return [
        {"key": row.entity_key, "type": row.entity_type, "name": row.entity_name}
        for row in rows
    ]


async def neo4j_traverse_simple(
    workspace_id: uuid.UUID,
    entity_keys: list[str],
    depth: int = 2,
    vault_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    """Variable-length path matching with optional vault_id edge filtering."""
    if not entity_keys:
        return []

    ws = str(workspace_id)
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )

    # Build WHERE clause for vault filtering on edges
    vault_filter = ""
    if vault_ids:
        vault_filter = "WHERE rel.vault_id IN $vault_ids"

    facts = []
    async with driver.session(database=settings.neo4j_database) as session:
        result = await session.run(
            """
            UNWIND $keys AS k
            MATCH (start {workspace_id: $ws, key: k})
            MATCH (start)-[r*1..""" + str(min(depth, 4)) + """]->(end)
            WITH start, r, end
            UNWIND r AS rel
            WITH startNode(rel) AS a, endNode(rel) AS b, rel, type(rel) AS rel_type
            """ + vault_filter + """
            RETURN DISTINCT
                a.name AS from_name,
                a.key AS from_key,
                rel_type,
                b.name AS to_name,
                b.key AS to_key,
                rel.document_id AS document_id,
                rel.evidence AS evidence
            LIMIT 100
            """,
            ws=ws,
            keys=entity_keys,
            vault_ids=[str(v) for v in vault_ids] if vault_ids else [],
        )
        records = await result.data()

    await driver.close()

    for rec in records:
        facts.append({
            "from_name": rec.get("from_name", ""),
            "from_key": rec.get("from_key", ""),
            "relation": rec.get("rel_type", ""),
            "to_name": rec.get("to_name", ""),
            "to_key": rec.get("to_key", ""),
            "document_id": rec.get("document_id", ""),
            "evidence": rec.get("evidence", ""),
        })

    return facts


async def enrich_chunks_with_docs(
    workspace_id: uuid.UUID, chunks: list[dict]
) -> list[dict]:
    """Add document metadata (title, url, source_type) to chunks."""
    doc_ids = list({uuid.UUID(c["document_id"]) for c in chunks})
    if not doc_ids:
        return chunks

    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(Document.id, Document.title, Document.url, Document.source_type)
            .where(Document.workspace_id == workspace_id, Document.id.in_(doc_ids))
        )
        rows = result.fetchall()

    doc_map = {str(r.id): {"title": r.title, "url": r.url, "source_type": r.source_type.value if r.source_type else None} for r in rows}

    for chunk in chunks:
        doc_info = doc_map.get(chunk["document_id"], {})
        chunk["doc_title"] = doc_info.get("title")
        chunk["doc_url"] = doc_info.get("url")
        chunk["doc_source_type"] = doc_info.get("source_type")

    return chunks


async def build_context(
    workspace_id: uuid.UUID,
    prompt: str,
    vault_ids: list[uuid.UUID] | None = None,
    depth: int = 2,
    top_k: int = 20,
) -> dict:
    """
    Full context building pipeline:
    1. Embed prompt
    2. Top-k chunk retrieval (vault-filtered)
    3. Seed entity lookup (vault-filtered)
    4. Neo4j traversal (vault-filtered edges)
    5. Return structured context
    """
    # 1. Embed prompt
    query_embedding = await embed_query(prompt)

    # 2. Top-k chunks
    chunks = await top_k_chunks(workspace_id, query_embedding, top_k, vault_ids)
    logger.info("Query found %d chunks for workspace=%s", len(chunks), workspace_id)

    if not chunks:
        return {"chunks": [], "facts": [], "seed_entities": []}

    # Enrich chunks with document metadata
    chunks = await enrich_chunks_with_docs(workspace_id, chunks)

    # 3. Seed entities from top chunks
    doc_ids = list({uuid.UUID(c["document_id"]) for c in chunks})
    seeds = await seed_entities(workspace_id, doc_ids, vault_ids)
    entity_keys = [s["key"] for s in seeds]
    logger.info("Found %d seed entities from top chunks", len(seeds))

    # 4. Neo4j traversal (use simple version without APOC)
    facts = []
    if entity_keys:
        try:
            facts = await neo4j_traverse_simple(workspace_id, entity_keys, depth, vault_ids)
            logger.info("Neo4j traversal returned %d facts", len(facts))
        except Exception as e:
            logger.warning("Neo4j traversal failed (continuing without graph): %s", e)

    return {
        "chunks": chunks,
        "facts": facts,
        "seed_entities": seeds,
    }
