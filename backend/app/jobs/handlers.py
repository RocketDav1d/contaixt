"""
Job type handlers. Each handler receives (workspace_id, payload_json).
"""

import logging
import uuid

from sqlalchemy import delete, func, insert, select

from app.db import get_async_session
from app.jobs.runner import register_handler
from app.models import Document, DocumentChunk, EntityMention, Job, JobStatus, JobType

logger = logging.getLogger(__name__)


async def _has_pending_job(workspace_id: uuid.UUID, job_type: JobType, document_id: str) -> bool:
    """Check if a queued/running job already exists for this document + type."""
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Job)
            .where(
                Job.workspace_id == workspace_id,
                Job.type == job_type,
                Job.status.in_([JobStatus.queued, JobStatus.running]),
                Job.payload_json["document_id"].as_string() == document_id,
            )
        )
        return bool(result.scalar_one() > 0)


async def handle_process_document(workspace_id: uuid.UUID, payload: dict) -> None:
    """Fan-out: enqueue CHUNK_DOCUMENT + EXTRACT_ENTITIES_RELATIONS for a document."""
    from app.jobs.enqueue import enqueue_job

    document_id = payload["document_id"]
    logger.info("PROCESS_DOCUMENT doc=%s", document_id)

    # Idempotency: skip if jobs already queued for this document
    for jt in (JobType.CHUNK_DOCUMENT, JobType.EXTRACT_ENTITIES_RELATIONS):
        if not await _has_pending_job(workspace_id, jt, document_id):
            await enqueue_job(workspace_id, jt, {"document_id": document_id})
        else:
            logger.info("PROCESS_DOCUMENT: skipping %s (already queued) doc=%s", jt.value, document_id)


async def handle_chunk_document(workspace_id: uuid.UUID, payload: dict) -> None:
    """Chunk document text, store chunks, enqueue EMBED_CHUNKS."""
    from app.jobs.enqueue import enqueue_job
    from app.processing.chunker import chunk_text

    document_id = uuid.UUID(payload["document_id"])
    logger.info("CHUNK_DOCUMENT doc=%s", document_id)

    Session = get_async_session()

    # Fetch document content
    async with Session() as session:
        result = await session.execute(
            select(Document).where(
                Document.id == document_id,
                Document.workspace_id == workspace_id,
            )
        )
        doc = result.scalar_one_or_none()

    if not doc or not doc.content_text:
        logger.warning("CHUNK_DOCUMENT: no content for doc=%s", document_id)
        return

    chunks = chunk_text(doc.content_text)
    if not chunks:
        logger.info("CHUNK_DOCUMENT: no chunks produced for doc=%s", document_id)
        return

    # Delete existing chunks for this document (re-processing support)
    async with Session() as session:
        await session.execute(
            delete(DocumentChunk).where(
                DocumentChunk.workspace_id == workspace_id,
                DocumentChunk.document_id == document_id,
            )
        )
        for ch in chunks:
            await session.execute(
                insert(DocumentChunk).values(
                    id=uuid.uuid4(),
                    workspace_id=workspace_id,
                    document_id=document_id,
                    idx=ch.idx,
                    text=ch.text,
                    start_offset=ch.start_offset,
                    end_offset=ch.end_offset,
                )
            )
        await session.commit()

    logger.info("CHUNK_DOCUMENT: stored %d chunks for doc=%s", len(chunks), document_id)

    await enqueue_job(workspace_id, JobType.EMBED_CHUNKS, {"document_id": str(document_id)})


async def handle_embed_chunks(workspace_id: uuid.UUID, payload: dict) -> None:
    """Embed chunks via OpenAI and store vectors in pgvector."""
    from app.processing.embeddings import embed_and_store

    document_id = uuid.UUID(payload["document_id"])
    logger.info("EMBED_CHUNKS doc=%s", document_id)

    count = await embed_and_store(workspace_id, document_id)
    logger.info("EMBED_CHUNKS: embedded %d chunks for doc=%s", count, document_id)


async def handle_extract_entities_relations(workspace_id: uuid.UUID, payload: dict) -> None:
    """LLM extraction of entities + relations, entity resolution, store mentions, enqueue graph upsert."""
    from app.jobs.enqueue import enqueue_job
    from app.processing.entity_resolution import resolve_entity_key
    from app.processing.extraction import extract_entities_relations

    document_id = uuid.UUID(payload["document_id"])
    logger.info("EXTRACT_ENTITIES_RELATIONS doc=%s", document_id)

    Session = get_async_session()

    # Fetch document
    async with Session() as session:
        result = await session.execute(
            select(Document).where(
                Document.id == document_id,
                Document.workspace_id == workspace_id,
            )
        )
        doc = result.scalar_one_or_none()

    if not doc or not doc.content_text:
        logger.warning("EXTRACT: no content for doc=%s", document_id)
        return

    # Extract entities and relations via LLM
    data = await extract_entities_relations(
        content_text=doc.content_text,
        title=doc.title or "",
        author_name=doc.author_name or "",
        author_email=doc.author_email or "",
        source_type=doc.source_type.value if doc.source_type else "",
    )

    entities = data.get("entities", [])
    relations = data.get("relations", [])

    if not entities:
        logger.info("EXTRACT: no entities found for doc=%s", document_id)
        return

    # Resolve entity keys
    entity_keys = {}
    for ent in entities:
        key = resolve_entity_key(ent)
        entity_keys[ent.get("name", "")] = key

    # Store entity mentions in Postgres
    async with Session() as session:
        # Delete existing mentions for re-processing
        await session.execute(
            delete(EntityMention).where(
                EntityMention.workspace_id == workspace_id,
                EntityMention.document_id == document_id,
            )
        )
        for ent in entities:
            name = ent.get("name", "")
            await session.execute(
                insert(EntityMention).values(
                    id=uuid.uuid4(),
                    workspace_id=workspace_id,
                    document_id=document_id,
                    entity_key=entity_keys.get(name, ""),
                    entity_type=ent.get("type", "unknown"),
                    entity_name=name,
                    confidence=1.0,
                )
            )
        await session.commit()

    logger.info(
        "EXTRACT: %d entities, %d relations for doc=%s",
        len(entities),
        len(relations),
        document_id,
    )

    # Enqueue graph upsert with extracted data
    await enqueue_job(
        workspace_id,
        JobType.UPSERT_GRAPH,
        {
            "document_id": str(document_id),
            "source_connection_id": str(doc.source_connection_id),
            "entities": entities,
            "relations": relations,
            "entity_keys": entity_keys,
        },
    )


async def handle_upsert_graph(workspace_id: uuid.UUID, payload: dict) -> None:
    """Upsert extracted entities/relations into Neo4j.

    The graph is now unified (no vault filtering on edges), but source_connection_id
    is stored on Document nodes to enable vault filtering during queries.
    """
    from app.processing.graph import upsert_entities_and_relations

    document_id = uuid.UUID(payload["document_id"])
    source_connection_id = uuid.UUID(payload["source_connection_id"]) if payload.get("source_connection_id") else None
    entities = payload.get("entities", [])
    relations = payload.get("relations", [])
    entity_keys = payload.get("entity_keys", {})

    logger.info("UPSERT_GRAPH doc=%s (%d entities, %d relations)", document_id, len(entities), len(relations))

    await upsert_entities_and_relations(
        workspace_id=workspace_id,
        document_id=document_id,
        source_connection_id=source_connection_id,
        entities=entities,
        relations=relations,
        entity_keys=entity_keys,
    )

    logger.info("UPSERT_GRAPH: done for doc=%s", document_id)


def register_all() -> None:
    register_handler("PROCESS_DOCUMENT", handle_process_document)
    register_handler("CHUNK_DOCUMENT", handle_chunk_document)
    register_handler("EMBED_CHUNKS", handle_embed_chunks)
    register_handler("EXTRACT_ENTITIES_RELATIONS", handle_extract_entities_relations)
    register_handler("UPSERT_GRAPH", handle_upsert_graph)
