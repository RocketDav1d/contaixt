"""
Context builder for GraphRAG queries using Neo4j unified vector + graph search.

Architecture:
1. Vector search on Chunk embeddings using Neo4j vector index (HNSW, cosine)
2. Graph traversal from chunks → documents → entities → related entities
3. Single database query combines semantic search with knowledge graph

Pre-filtering approach for multi-tenant isolation:
- Uses exact nearest neighbor (ENN) with vector.similarity.cosine() for workspace/vault filtering
- Guarantees workspace isolation before vector similarity computation
- Reference: https://neo4j.com/developer/genai-ecosystem/vector-search/

Driver management:
- Uses singleton driver from neo4j_client for connection pooling
- Reference: https://neo4j.com/blog/developer/neo4j-driver-best-practices/
"""

import logging
import uuid

import cohere
from openai import AsyncOpenAI
from sqlalchemy import select

from app.config import settings
from app.db import get_async_session
from app.models import Document, VaultSourceConnection
from app.neo4j_client import get_session

logger = logging.getLogger(__name__)

EMBED_MODEL = "text-embedding-3-small"
RERANK_MODEL = "rerank-v3.5"
RERANK_CANDIDATE_MULTIPLIER = 3  # Fetch 3x candidates, then rerank to top_k


async def get_connection_ids_for_vaults(vault_ids: list[uuid.UUID]) -> list[uuid.UUID]:
    """Get all source_connection_ids assigned to the given vaults."""
    if not vault_ids:
        return []

    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(VaultSourceConnection.source_connection_id)
            .where(VaultSourceConnection.vault_id.in_(vault_ids))
            .distinct()
        )
        return [row[0] for row in result.fetchall()]


async def embed_query(query: str) -> list[float]:
    """Embed a query string via OpenAI."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resp = await client.embeddings.create(input=[query], model=EMBED_MODEL)
    return resp.data[0].embedding


async def rerank_chunks(
    query: str,
    chunks: list[dict],
    top_k: int = 20,
) -> list[dict]:
    """
    Rerank chunks using Cohere's rerank API for improved relevance.

    Two-stage retrieval:
    1. Fast vector search returns candidates (already done)
    2. Precise reranking scores each candidate against the query

    Returns top_k chunks sorted by relevance score.
    """
    if not chunks or not settings.cohere_api_key:
        return chunks[:top_k]

    try:
        co = cohere.Client(api_key=settings.cohere_api_key)
        documents = [chunk["text"] for chunk in chunks]

        response = co.rerank(
            model=RERANK_MODEL,
            query=query,
            documents=documents,
            top_n=min(top_k, len(chunks)),
            return_documents=False,
        )

        reranked_chunks = []
        for result in response.results:
            chunk = chunks[result.index].copy()
            chunk["rerank_score"] = result.relevance_score
            reranked_chunks.append(chunk)

        logger.info(
            "Reranked %d candidates to %d results (top score: %.3f)",
            len(chunks),
            len(reranked_chunks),
            reranked_chunks[0]["rerank_score"] if reranked_chunks else 0,
        )
        return reranked_chunks

    except Exception as e:
        logger.warning("Reranking failed, falling back to vector results: %s", e)
        return chunks[:top_k]


async def vector_search_chunks(
    workspace_id: uuid.UUID,
    query_embedding: list[float],
    top_k: int = 20,
    connection_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    """
    Vector similarity search on Chunk nodes with pre-filtering.

    Uses exact nearest neighbor (ENN) with vector.similarity.cosine() to enable
    pre-filtering by workspace_id and optionally connection_ids (for vault filtering).

    This ensures multi-tenant isolation: workspace filter is applied BEFORE
    similarity computation, not after.

    Reference: https://neo4j.com/developer/genai-ecosystem/vector-search/
    """
    ws = str(workspace_id)
    conn_ids = [str(c) for c in connection_ids] if connection_ids else None

    # Build the pre-filter query using ENN approach
    # This applies workspace/vault filter BEFORE computing similarity
    if conn_ids:
        query = """
        MATCH (chunk:Chunk)
        WHERE chunk.workspace_id = $ws
          AND chunk.source_connection_id IN $conn_ids
          AND chunk.embedding IS NOT NULL
        WITH chunk, vector.similarity.cosine(chunk.embedding, $embedding) AS score
        WHERE score > 0.0
        ORDER BY score DESC
        LIMIT $top_k
        RETURN chunk.chunk_id AS chunk_id,
               chunk.document_id AS document_id,
               chunk.idx AS idx,
               chunk.text AS text,
               chunk.start_offset AS start_offset,
               chunk.end_offset AS end_offset,
               score
        """
        params = {"ws": ws, "conn_ids": conn_ids, "embedding": query_embedding, "top_k": top_k}
    else:
        query = """
        MATCH (chunk:Chunk)
        WHERE chunk.workspace_id = $ws
          AND chunk.embedding IS NOT NULL
        WITH chunk, vector.similarity.cosine(chunk.embedding, $embedding) AS score
        WHERE score > 0.0
        ORDER BY score DESC
        LIMIT $top_k
        RETURN chunk.chunk_id AS chunk_id,
               chunk.document_id AS document_id,
               chunk.idx AS idx,
               chunk.text AS text,
               chunk.start_offset AS start_offset,
               chunk.end_offset AS end_offset,
               score
        """
        params = {"ws": ws, "embedding": query_embedding, "top_k": top_k}

    try:
        async with get_session() as session:
            result = await session.run(query, **params)
            records = await result.data()

        chunks = [
            {
                "chunk_id": r["chunk_id"],
                "document_id": r["document_id"],
                "idx": r["idx"],
                "text": r["text"],
                "start_offset": r["start_offset"],
                "end_offset": r["end_offset"],
                "score": r["score"],
                "distance": 1 - r["score"],  # Convert similarity to distance for compatibility
            }
            for r in records
        ]

        logger.info("Vector search found %d chunks for workspace=%s", len(chunks), workspace_id)
        return chunks

    except Exception as e:
        logger.error("Vector search failed: %s", e)
        return []


async def get_seed_entities(
    workspace_id: uuid.UUID,
    document_ids: list[str],
) -> list[dict]:
    """
    Get entities mentioned in the given documents via MENTIONS edges.
    """
    if not document_ids:
        return []

    ws = str(workspace_id)

    query = """
    UNWIND $doc_ids AS doc_id
    MATCH (d:Document {workspace_id: $ws, key: 'doc:' + doc_id})-[:MENTIONS]->(entity)
    RETURN DISTINCT entity.key AS key,
                    labels(entity)[0] AS type,
                    entity.name AS name
    """

    try:
        async with get_session() as session:
            result = await session.run(query, ws=ws, doc_ids=document_ids)
            records = await result.data()

        entities = [
            {"key": r["key"], "type": r["type"], "name": r["name"]}
            for r in records
            if r.get("key")
        ]

        logger.info("Found %d seed entities from %d documents", len(entities), len(document_ids))
        return entities

    except Exception as e:
        logger.error("Seed entity lookup failed: %s", e)
        return []


async def traverse_graph(
    workspace_id: uuid.UUID,
    entity_keys: list[str],
    depth: int = 2,
) -> list[dict]:
    """
    Traverse the knowledge graph from seed entities.

    Uses variable-length path matching to find related entities and facts.
    The graph is workspace-unified (no vault filtering on edges) to enable
    cross-vault knowledge discovery.
    """
    if not entity_keys:
        return []

    ws = str(workspace_id)
    max_depth = min(depth, 3)  # Cap depth for performance

    query = """
    UNWIND $keys AS k
    MATCH (start {workspace_id: $ws, key: k})
    MATCH (start)-[r*1..{depth}]->(end)
    WITH start, r, end
    UNWIND r AS rel
    WITH startNode(rel) AS a, endNode(rel) AS b, rel, type(rel) AS rel_type
    RETURN DISTINCT
        a.name AS from_name,
        a.key AS from_key,
        rel_type AS relation,
        b.name AS to_name,
        b.key AS to_key,
        rel.document_id AS document_id,
        rel.evidence AS evidence
    LIMIT 100
    """.replace("{depth}", str(max_depth))

    try:
        async with get_session() as session:
            result = await session.run(query, ws=ws, keys=entity_keys)
            records = await result.data()

        facts = [
            {
                "from_name": r.get("from_name", ""),
                "from_key": r.get("from_key", ""),
                "relation": r.get("relation", ""),
                "to_name": r.get("to_name", ""),
                "to_key": r.get("to_key", ""),
                "document_id": r.get("document_id", ""),
                "evidence": r.get("evidence", ""),
            }
            for r in records
            if r.get("from_key")
        ]

        logger.info("Graph traversal found %d facts from %d seed entities", len(facts), len(entity_keys))
        return facts

    except Exception as e:
        logger.error("Graph traversal failed: %s", e)
        return []


async def enrich_chunks_with_docs(workspace_id: uuid.UUID, chunks: list[dict]) -> list[dict]:
    """Add document metadata (title, url, source_type) to chunks from PostgreSQL."""
    doc_ids = list({uuid.UUID(c["document_id"]) for c in chunks if c.get("document_id")})
    if not doc_ids:
        return chunks

    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(Document.id, Document.title, Document.url, Document.source_type).where(
                Document.workspace_id == workspace_id, Document.id.in_(doc_ids)
            )
        )
        rows = result.fetchall()

    doc_map = {
        str(r.id): {"title": r.title, "url": r.url, "source_type": r.source_type.value if r.source_type else None}
        for r in rows
    }

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
    Full context building pipeline using Neo4j vector + graph search.

    Pipeline:
    1. Embed prompt via OpenAI
    2. Resolve vault_ids to connection_ids (if filtering)
    3. Vector search with pre-filtering (ENN for workspace/vault isolation)
    4. Rerank with Cohere for precision
    5. Get seed entities from matching documents
    6. Traverse knowledge graph from seeds
    7. Enrich with document metadata from PostgreSQL

    Returns:
        {
            "chunks": [...],        # Top chunks with similarity scores
            "facts": [...],         # Graph relationships from traversal
            "seed_entities": [...]  # Entities found in matching documents
        }
    """
    # 1. Embed prompt
    query_embedding = await embed_query(prompt)

    # 2. Resolve vault filtering
    connection_ids = None
    if vault_ids:
        connection_ids = await get_connection_ids_for_vaults(vault_ids)
        if not connection_ids:
            return {"chunks": [], "facts": [], "seed_entities": []}

    # 3. Vector search with pre-filtering
    candidate_count = top_k * RERANK_CANDIDATE_MULTIPLIER
    chunks = await vector_search_chunks(
        workspace_id=workspace_id,
        query_embedding=query_embedding,
        top_k=candidate_count,
        connection_ids=connection_ids,
    )

    if not chunks:
        return {"chunks": [], "facts": [], "seed_entities": []}

    # 4. Rerank candidates
    chunks = await rerank_chunks(prompt, chunks, top_k)

    # 5. Get seed entities from matching documents
    doc_ids = list({c["document_id"] for c in chunks})
    seed_entities = await get_seed_entities(workspace_id, doc_ids)

    # 6. Traverse knowledge graph
    entity_keys = [e["key"] for e in seed_entities]
    facts = await traverse_graph(workspace_id, entity_keys, depth)

    # 7. Enrich with document metadata
    chunks = await enrich_chunks_with_docs(workspace_id, chunks)

    logger.info(
        "Context built: %d chunks, %d facts, %d entities for workspace=%s",
        len(chunks), len(facts), len(seed_entities), workspace_id
    )

    return {
        "chunks": chunks,
        "facts": facts,
        "seed_entities": seed_entities,
    }
