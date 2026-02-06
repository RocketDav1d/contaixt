"""
Context builder for GraphRAG queries.

1. Embed prompt → multi-vector search over evidence/entity/relation chunks
2. Expand with linked evidence chunks and rerank by composite score
3. Seed entities from chunks + query entities
4. Neo4j traversal from seed entities up to `depth`
5. Return evidence chunks + graph facts for the answer composer
"""

import logging
import uuid

from neo4j import AsyncGraphDatabase
from openai import AsyncOpenAI
from sqlalchemy import func, select, text

from app.config import settings
from app.db import get_async_session
from app.models import ChunkType, Document, DocumentChunk, EntityMention
from app.processing.extraction import extract_query_entities

logger = logging.getLogger(__name__)

EMBED_MODEL = "text-embedding-3-small"


async def embed_query(query: str) -> list[float]:
    """Embed a query string via OpenAI."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resp = await client.embeddings.create(input=[query], model=EMBED_MODEL)
    return resp.data[0].embedding


async def top_k_chunks_by_type(
    workspace_id: uuid.UUID,
    query_embedding: list[float],
    chunk_type: ChunkType,
    top_k: int = 20,
    vault_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    """Retrieve top-k similar chunks by type using multi-vector embeddings."""
    Session = get_async_session()
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    if vault_ids:
        sql = text("""
            WITH ranked AS (
                SELECT
                    ce.chunk_id,
                    MIN(ce.embedding <=> :embedding) AS distance
                FROM chunk_embeddings ce
                JOIN document_chunks dc ON dc.id = ce.chunk_id
                WHERE dc.workspace_id = :ws
                  AND dc.vault_id = ANY(:vault_ids)
                  AND dc.chunk_type = :chunk_type
                GROUP BY ce.chunk_id
                ORDER BY distance
                LIMIT :top_k
            )
            SELECT
                dc.id, dc.document_id, dc.idx, dc.text,
                dc.start_offset, dc.end_offset,
                dc.chunk_type, dc.chunk_key, dc.metadata_json,
                ranked.distance
            FROM ranked
            JOIN document_chunks dc ON dc.id = ranked.chunk_id
            ORDER BY ranked.distance
        """)
        params = {
            "ws": str(workspace_id),
            "embedding": embedding_str,
            "top_k": top_k,
            "vault_ids": [str(v) for v in vault_ids],
            "chunk_type": chunk_type.value,
        }
    else:
        sql = text("""
            WITH ranked AS (
                SELECT
                    ce.chunk_id,
                    MIN(ce.embedding <=> :embedding) AS distance
                FROM chunk_embeddings ce
                JOIN document_chunks dc ON dc.id = ce.chunk_id
                WHERE dc.workspace_id = :ws
                  AND dc.chunk_type = :chunk_type
                GROUP BY ce.chunk_id
                ORDER BY distance
                LIMIT :top_k
            )
            SELECT
                dc.id, dc.document_id, dc.idx, dc.text,
                dc.start_offset, dc.end_offset,
                dc.chunk_type, dc.chunk_key, dc.metadata_json,
                ranked.distance
            FROM ranked
            JOIN document_chunks dc ON dc.id = ranked.chunk_id
            ORDER BY ranked.distance
        """)
        params = {
            "ws": str(workspace_id),
            "embedding": embedding_str,
            "top_k": top_k,
            "chunk_type": chunk_type.value,
        }

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
            "chunk_type": row.chunk_type,
            "chunk_key": row.chunk_key,
            "metadata_json": row.metadata_json,
            "distance": row.distance,
        })

    return chunks


async def fetch_chunks_by_ids(
    workspace_id: uuid.UUID,
    chunk_ids: list[uuid.UUID],
    chunk_type: ChunkType | None = None,
) -> list[dict]:
    """Fetch chunks by id."""
    if not chunk_ids:
        return []
    Session = get_async_session()
    async with Session() as session:
        stmt = select(DocumentChunk).where(
            DocumentChunk.workspace_id == workspace_id,
            DocumentChunk.id.in_(chunk_ids),
        )
        if chunk_type:
            stmt = stmt.where(DocumentChunk.chunk_type == chunk_type)
        result = await session.execute(stmt)
        rows = result.scalars().all()

    return [
        {
            "chunk_id": str(r.id),
            "document_id": str(r.document_id),
            "idx": r.idx,
            "text": r.text,
            "start_offset": r.start_offset,
            "end_offset": r.end_offset,
            "chunk_type": r.chunk_type,
            "chunk_key": r.chunk_key,
            "metadata_json": r.metadata_json,
        }
        for r in rows
    ]


async def chunk_distances(
    workspace_id: uuid.UUID,
    query_embedding: list[float],
    chunk_ids: list[uuid.UUID],
) -> dict[str, float]:
    """Compute min vector distance for specific chunks."""
    if not chunk_ids:
        return {}
    Session = get_async_session()
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    sql = text("""
        SELECT
            ce.chunk_id,
            MIN(ce.embedding <=> :embedding) AS distance
        FROM chunk_embeddings ce
        JOIN document_chunks dc ON dc.id = ce.chunk_id
        WHERE dc.workspace_id = :ws
          AND ce.chunk_id = ANY(:chunk_ids)
        GROUP BY ce.chunk_id
    """)
    params = {"ws": str(workspace_id), "embedding": embedding_str, "chunk_ids": [str(c) for c in chunk_ids]}
    async with Session() as session:
        result = await session.execute(sql, params)
        rows = result.fetchall()
    return {str(r.chunk_id): r.distance for r in rows}


async def seed_entities(
    workspace_id: uuid.UUID,
    chunk_ids: list[uuid.UUID] | None = None,
    document_ids: list[uuid.UUID] | None = None,
    vault_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    """Get entity keys mentioned in the given chunks or documents."""
    if not chunk_ids and not document_ids:
        return []

    Session = get_async_session()
    async with Session() as session:
        stmt = (
            select(
                EntityMention.entity_key,
                EntityMention.entity_type,
                EntityMention.entity_name,
            )
            .where(EntityMention.workspace_id == workspace_id)
            .distinct(EntityMention.entity_key)
        )
        if chunk_ids:
            stmt = stmt.where(EntityMention.chunk_id.in_(chunk_ids))
        elif document_ids:
            stmt = stmt.where(EntityMention.document_id.in_(document_ids))
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


async def lookup_entity_keys_by_name(
    workspace_id: uuid.UUID,
    names: list[str],
) -> list[dict]:
    """Resolve entity keys in Neo4j by exact name match (case-insensitive)."""
    if not names:
        return []
    ws = str(workspace_id)
    lowered = [n.lower() for n in names if n]
    if not lowered:
        return []

    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )
    async with driver.session(database=settings.neo4j_database) as session:
        result = await session.run(
            """
            UNWIND $names AS n
            MATCH (e {workspace_id: $ws})
            WHERE toLower(e.name) = n
            RETURN DISTINCT e.key AS key, e.name AS name, labels(e) AS labels
            """,
            ws=ws,
            names=lowered,
        )
        records = await result.data()
    await driver.close()

    seeds = []
    for rec in records:
        labels = rec.get("labels") or []
        etype = labels[0] if labels else "Unknown"
        seeds.append({"key": rec.get("key", ""), "type": etype, "name": rec.get("name", "")})
    return seeds


async def entity_confidence_by_chunk(
    workspace_id: uuid.UUID,
    chunk_ids: list[uuid.UUID],
    vault_ids: list[uuid.UUID] | None = None,
) -> dict[str, float]:
    """Return max mention confidence per chunk."""
    if not chunk_ids:
        return {}
    Session = get_async_session()
    async with Session() as session:
        stmt = (
            select(
                EntityMention.chunk_id,
                func.max(EntityMention.confidence).label("confidence"),
            )
            .where(
                EntityMention.workspace_id == workspace_id,
                EntityMention.chunk_id.in_(chunk_ids),
            )
            .group_by(EntityMention.chunk_id)
        )
        if vault_ids:
            stmt = stmt.where(EntityMention.vault_id.in_(vault_ids))
        result = await session.execute(stmt)
        rows = result.fetchall()
    return {str(r.chunk_id): float(r.confidence or 0.0) for r in rows}


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

    # 2. Composite retrieval (evidence + entity + relation chunks)
    entity_top_k = max(5, top_k // 2)
    relation_top_k = max(5, top_k // 2)
    evidence_chunks = await top_k_chunks_by_type(
        workspace_id, query_embedding, ChunkType.evidence, top_k, vault_ids
    )
    entity_chunks = await top_k_chunks_by_type(
        workspace_id, query_embedding, ChunkType.entity, entity_top_k, vault_ids
    )
    relation_chunks = await top_k_chunks_by_type(
        workspace_id, query_embedding, ChunkType.relation, relation_top_k, vault_ids
    )
    logger.info(
        "Query found %d evidence, %d entity, %d relation chunks for workspace=%s",
        len(evidence_chunks),
        len(entity_chunks),
        len(relation_chunks),
        workspace_id,
    )

    if not evidence_chunks and not entity_chunks and not relation_chunks:
        return {"chunks": [], "facts": [], "seed_entities": []}

    # 3. Pull evidence chunks linked from entity/relation chunks
    linked_evidence_ids: set[uuid.UUID] = set()
    for c in entity_chunks + relation_chunks:
        meta = c.get("metadata_json") or {}
        for cid in meta.get("evidence_chunk_ids", []):
            try:
                linked_evidence_ids.add(uuid.UUID(cid))
            except (ValueError, TypeError):
                continue

    linked_evidence_chunks = await fetch_chunks_by_ids(
        workspace_id, list(linked_evidence_ids), chunk_type=ChunkType.evidence
    )

    evidence_map = {c["chunk_id"]: c for c in evidence_chunks}
    for c in linked_evidence_chunks:
        evidence_map.setdefault(c["chunk_id"], c)

    evidence_chunks_all = list(evidence_map.values())

    # 4. Distances for all evidence chunks
    distance_map = {c["chunk_id"]: c.get("distance") for c in evidence_chunks if c.get("distance") is not None}
    missing_ids = []
    for cid in evidence_map.keys():
        if cid not in distance_map:
            try:
                missing_ids.append(uuid.UUID(cid))
            except ValueError:
                continue
    distance_map.update(await chunk_distances(workspace_id, query_embedding, missing_ids))

    # 5. Evidence confidence + graph proximity scoring
    evidence_uuid_ids = []
    for cid in evidence_map.keys():
        try:
            evidence_uuid_ids.append(uuid.UUID(cid))
        except ValueError:
            continue

    mention_conf_map = await entity_confidence_by_chunk(workspace_id, evidence_uuid_ids, vault_ids)

    relation_conf_map: dict[str, float] = {}
    for rel in relation_chunks:
        meta = rel.get("metadata_json") or {}
        qualifiers = meta.get("qualifiers") or {}
        conf_val = qualifiers.get("confidence")
        try:
            conf_val = float(conf_val) if conf_val is not None else 0.0
        except (TypeError, ValueError):
            conf_val = 0.0
        for cid in meta.get("evidence_chunk_ids", []):
            relation_conf_map[cid] = max(relation_conf_map.get(cid, 0.0), conf_val)

    linked_evidence_str_ids = {str(cid) for cid in linked_evidence_ids}
    scored_evidence = []
    for c in evidence_chunks_all:
        cid = c["chunk_id"]
        dist = distance_map.get(cid)
        similarity = 1.0 / (1.0 + dist) if dist is not None else 0.0
        graph_proximity = 1.0 if cid in linked_evidence_str_ids else 0.0
        evidence_confidence = max(mention_conf_map.get(cid, 0.0), relation_conf_map.get(cid, 0.0))
        score = similarity + graph_proximity + evidence_confidence
        c["distance"] = dist
        c["score"] = score
        scored_evidence.append(c)

    scored_evidence.sort(key=lambda c: (-c["score"], c["distance"] if c["distance"] is not None else 1e9))
    evidence_final = scored_evidence[:top_k]

    # Enrich evidence chunks with document metadata
    evidence_final = await enrich_chunks_with_docs(workspace_id, evidence_final)

    # 6. Seed entities (evidence mentions + entity/relation chunks + query entities)
    mention_seeds = await seed_entities(workspace_id, chunk_ids=evidence_uuid_ids, vault_ids=vault_ids)

    entity_chunk_seeds = []
    for c in entity_chunks:
        meta = c.get("metadata_json") or {}
        key = meta.get("entity_key")
        if key:
            entity_chunk_seeds.append({
                "key": key,
                "type": meta.get("entity_type") or "Unknown",
                "name": meta.get("entity_name") or "",
            })

    relation_chunk_seeds = []
    for c in relation_chunks:
        meta = c.get("metadata_json") or {}
        from_key = meta.get("from_key")
        to_key = meta.get("to_key")
        from_name = meta.get("from_name") or ""
        to_name = meta.get("to_name") or ""
        if from_key:
            relation_chunk_seeds.append({"key": from_key, "type": "Unknown", "name": from_name})
        if to_key:
            relation_chunk_seeds.append({"key": to_key, "type": "Unknown", "name": to_name})

    query_entities = await extract_query_entities(prompt)
    query_names = [e.get("name", "") for e in query_entities if e.get("name")]
    name_seeds = await lookup_entity_keys_by_name(workspace_id, query_names)

    # Merge seeds by key
    seeds_map: dict[str, dict] = {}
    for seed in mention_seeds + entity_chunk_seeds + relation_chunk_seeds + name_seeds:
        key = seed.get("key")
        if not key:
            continue
        existing = seeds_map.get(key)
        if not existing:
            seeds_map[key] = seed
        else:
            if not existing.get("name") and seed.get("name"):
                existing["name"] = seed.get("name")
            if (existing.get("type") in (None, "", "Unknown")) and seed.get("type"):
                existing["type"] = seed.get("type")

    seeds = list(seeds_map.values())
    entity_keys = [s["key"] for s in seeds]
    logger.info("Found %d seed entities", len(seeds))

    # 7. Neo4j traversal
    facts = []
    if entity_keys:
        try:
            facts = await neo4j_traverse_simple(workspace_id, entity_keys, depth, vault_ids)
            logger.info("Neo4j traversal returned %d facts", len(facts))
        except Exception as e:
            logger.warning("Neo4j traversal failed (continuing without graph): %s", e)

    return {
        "chunks": evidence_final,
        "facts": facts,
        "seed_entities": seeds,
        "entity_chunks": entity_chunks,
        "relation_chunks": relation_chunks,
    }
