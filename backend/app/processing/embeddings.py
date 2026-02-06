"""
OpenAI embeddings writer. Embeds chunk texts (multi-vector per chunk) and stores vectors in pgvector.
"""

import logging
import uuid

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.config import settings
from app.db import get_async_session
from app.models import ChunkEmbedding, ChunkType, DocumentChunk

logger = logging.getLogger(__name__)

MODEL = "text-embedding-3-small"
BATCH_SIZE = 50  # OpenAI allows up to 2048 inputs, but keep batches manageable


def _required_embedding_kinds(chunk: DocumentChunk) -> dict[str, str]:
    """Return embedding-kind -> text for a chunk."""
    if chunk.chunk_type == ChunkType.evidence:
        return {"text": chunk.text}

    metadata = chunk.metadata_json or {}

    if chunk.chunk_type == ChunkType.entity:
        payload = {"summary": chunk.text}
        aliases = metadata.get("aliases") or []
        if aliases:
            payload["aliases"] = f"Aliases: {', '.join(aliases)}"
        return payload

    if chunk.chunk_type == ChunkType.relation:
        relation_type = metadata.get("relation_type") or ""
        from_name = metadata.get("from_name") or ""
        to_name = metadata.get("to_name") or ""
        qualifiers = metadata.get("qualifiers") or {}
        qual_parts = []
        if qualifiers.get("time"):
            qual_parts.append(f"time={qualifiers.get('time')}")
        if qualifiers.get("location"):
            qual_parts.append(f"location={qualifiers.get('location')}")
        if qualifiers.get("confidence") is not None:
            qual_parts.append(f"confidence={qualifiers.get('confidence')}")
        qual_text = f"Qualifiers: {', '.join(qual_parts)}" if qual_parts else ""
        relation_text = f"Relation: {from_name} --{relation_type}--> {to_name}\n{qual_text}".strip()
        payload = {"relation": relation_text}
        evidence_texts = metadata.get("evidence_texts") or []
        if evidence_texts:
            payload["evidence"] = evidence_texts[-1]
        return payload

    return {}


async def embed_and_store(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    chunk_ids: list[uuid.UUID] | None = None,
    force: bool = False,
) -> int:
    """Embed chunks and store vectors. Returns count embedded."""
    Session = get_async_session()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    async with Session() as session:
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.workspace_id == workspace_id)
            .order_by(DocumentChunk.idx)
        )
        if chunk_ids:
            stmt = stmt.where(DocumentChunk.id.in_(chunk_ids))
        else:
            stmt = stmt.where(DocumentChunk.document_id == document_id)
        result = await session.execute(stmt)
        chunks = list(result.scalars().all())

    if not chunks:
        return 0

    # Build embedding requests
    requests: list[tuple[DocumentChunk, str, str]] = []
    for ch in chunks:
        kinds = _required_embedding_kinds(ch)
        for kind, text in kinds.items():
            if not text:
                continue
            requests.append((ch, kind, text))

    if not requests:
        return 0

    # If not forcing, skip embedding kinds that already exist
    if not force:
        async with Session() as session:
            result = await session.execute(
                select(ChunkEmbedding.chunk_id, ChunkEmbedding.kind).where(
                    ChunkEmbedding.chunk_id.in_([c.id for c, _, _ in requests])
                )
            )
            existing = {(str(r.chunk_id), r.kind) for r in result.fetchall()}
        requests = [
            (ch, kind, text)
            for ch, kind, text in requests
            if (str(ch.id), kind) not in existing
        ]

    if not requests:
        return 0

    embedded = 0
    for i in range(0, len(requests), BATCH_SIZE):
        batch = requests[i : i + BATCH_SIZE]
        texts = [t for _, _, t in batch]

        resp = await client.embeddings.create(input=texts, model=MODEL)

        async with Session() as session:
            for (chunk, kind, _), emb_data in zip(batch, resp.data):
                stmt = insert(ChunkEmbedding).values(
                    id=uuid.uuid4(),
                    workspace_id=chunk.workspace_id,
                    vault_id=chunk.vault_id,
                    document_id=chunk.document_id,
                    chunk_id=chunk.id,
                    kind=kind,
                    embedding=emb_data.embedding,
                ).on_conflict_do_update(
                    index_elements=["chunk_id", "kind"],
                    set_={"embedding": emb_data.embedding},
                )
                await session.execute(stmt)
            await session.commit()

        embedded += len(batch)
        logger.info("Embedded batch %d-%d for doc=%s", i, i + len(batch), document_id)

    return embedded
