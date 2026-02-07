"""
OpenAI embeddings writer. Embeds chunk texts and stores vectors in pgvector.
"""

import logging
import uuid

from openai import AsyncOpenAI
from sqlalchemy import update

from app.config import settings
from app.db import get_async_session
from app.models import DocumentChunk

logger = logging.getLogger(__name__)

MODEL = "text-embedding-3-small"
BATCH_SIZE = 50  # OpenAI allows up to 2048 inputs, but keep batches manageable


async def embed_and_store(workspace_id: uuid.UUID, document_id: uuid.UUID) -> int:
    """Embed all chunks for a document and store vectors. Returns count embedded."""
    Session = get_async_session()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    async with Session() as session:
        from sqlalchemy import select

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
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c.text for c in batch]

        resp = await client.embeddings.create(input=texts, model=MODEL)

        async with Session() as session:
            for chunk, emb_data in zip(batch, resp.data, strict=True):
                await session.execute(
                    update(DocumentChunk).where(DocumentChunk.id == chunk.id).values(embedding=emb_data.embedding)
                )
            await session.commit()

        embedded += len(batch)
        logger.info("Embedded batch %d-%d for doc=%s", i, i + len(batch), document_id)

    return embedded
