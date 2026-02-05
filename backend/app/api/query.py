"""
POST /v1/query – GraphRAG query endpoint.

Flow:
1. Embed prompt → pgvector similarity search
2. Seed entities from entity_mentions
3. Neo4j traversal for graph facts
4. LLM answer constrained to provided context
5. Return answer + citations
"""

import logging
import uuid

from fastapi import APIRouter
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import settings
from app.processing.context_builder import build_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["query"])


class QueryRequest(BaseModel):
    workspace_id: uuid.UUID
    prompt: str
    depth: int = 2
    top_k_chunks: int = 20


class Citation(BaseModel):
    url: str | None = None
    title: str | None = None
    quote: str | None = None
    document_id: str | None = None
    chunk_id: str | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    debug: dict | None = None


SYSTEM_PROMPT = """You are a knowledge assistant. Answer the user's question using ONLY the provided context.

Context consists of:
1. CHUNKS: Relevant text excerpts from documents (each has a [CHUNK_ID])
2. FACTS: Knowledge graph relationships between entities

Rules:
- Only use information present in the context. Do not use prior knowledge.
- If the context doesn't contain enough information, say so honestly.
- When you use information from a chunk, cite it by including the chunk_id in square brackets, e.g. [chunk-abc123].
- Be concise and direct.
- Answer in the same language as the user's question.

Return your answer as valid JSON with this schema:
{
  "answer": "Your answer with [chunk-id] citations inline...",
  "cited_chunk_ids": ["chunk-id-1", "chunk-id-2"]
}"""


def _build_context_prompt(chunks: list[dict], facts: list[dict]) -> str:
    """Format chunks and facts into a context string for the LLM."""
    parts = []

    if chunks:
        parts.append("=== CHUNKS ===")
        for c in chunks:
            title = c.get("doc_title") or "untitled"
            source = c.get("doc_source_type") or "unknown"
            parts.append(f"[{c['chunk_id']}] (source: {source}, doc: {title})")
            parts.append(c["text"])
            parts.append("")

    if facts:
        parts.append("=== KNOWLEDGE GRAPH FACTS ===")
        for f in facts:
            evidence = f" (evidence: {f['evidence'][:100]})" if f.get("evidence") else ""
            parts.append(f"- {f['from_name']} --[{f['relation']}]--> {f['to_name']}{evidence}")
        parts.append("")

    return "\n".join(parts)


@router.post("/query", response_model=QueryResponse)
async def query(body: QueryRequest):
    # 1-4. Build context
    ctx = await build_context(
        workspace_id=body.workspace_id,
        prompt=body.prompt,
        depth=body.depth,
        top_k=body.top_k_chunks,
    )

    chunks = ctx["chunks"]
    facts = ctx["facts"]

    if not chunks:
        return QueryResponse(
            answer="Keine relevanten Dokumente gefunden. Bitte stelle sicher, dass Dokumente verarbeitet wurden.",
            citations=[],
            debug={"chunks_found": 0, "facts_found": 0, "seed_entities": []},
        )

    # 5. LLM answer with citations
    context_text = _build_context_prompt(chunks, facts)

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {body.prompt}"},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    import json
    raw = resp.choices[0].message.content or "{}"
    try:
        llm_result = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM answer JSON: %s", raw[:200])
        llm_result = {"answer": raw, "cited_chunk_ids": []}

    answer_text = llm_result.get("answer", "")
    cited_ids = set(llm_result.get("cited_chunk_ids", []))

    # Build citations from cited chunks
    chunk_map = {c["chunk_id"]: c for c in chunks}
    citations = []
    for cid in cited_ids:
        c = chunk_map.get(cid)
        if c:
            citations.append(Citation(
                url=c.get("doc_url"),
                title=c.get("doc_title"),
                quote=c["text"][:200],
                document_id=c["document_id"],
                chunk_id=cid,
            ))

    logger.info(
        "Query answered: %d chunks, %d facts, %d citations",
        len(chunks), len(facts), len(citations),
    )

    return QueryResponse(
        answer=answer_text,
        citations=citations,
        debug={
            "chunks_found": len(chunks),
            "facts_found": len(facts),
            "seed_entities": [s["name"] for s in ctx["seed_entities"]],
        },
    )
