"""
Job type handlers. Each handler receives (workspace_id, payload_json).
Implementations will be filled in during Phase 6 (Processing).
"""

import logging
import uuid

from app.jobs.runner import register_handler

logger = logging.getLogger(__name__)


async def handle_process_document(workspace_id: uuid.UUID, payload: dict) -> None:
    """Fan-out: enqueue CHUNK_DOCUMENT + EXTRACT_ENTITIES_RELATIONS for a document."""
    from app.jobs.enqueue import enqueue_job
    from app.models import JobType

    document_id = payload["document_id"]
    logger.info("PROCESS_DOCUMENT doc=%s", document_id)

    await enqueue_job(workspace_id, JobType.CHUNK_DOCUMENT, {"document_id": document_id})
    await enqueue_job(workspace_id, JobType.EXTRACT_ENTITIES_RELATIONS, {"document_id": document_id})


async def handle_chunk_document(workspace_id: uuid.UUID, payload: dict) -> None:
    """Chunk document text and store chunks. Then enqueue EMBED_CHUNKS."""
    logger.info("CHUNK_DOCUMENT doc=%s – not yet implemented", payload["document_id"])


async def handle_embed_chunks(workspace_id: uuid.UUID, payload: dict) -> None:
    """Embed chunks via OpenAI and store vectors in pgvector."""
    logger.info("EMBED_CHUNKS doc=%s – not yet implemented", payload["document_id"])


async def handle_extract_entities_relations(workspace_id: uuid.UUID, payload: dict) -> None:
    """LLM extraction of entities + relations from document."""
    logger.info("EXTRACT_ENTITIES_RELATIONS doc=%s – not yet implemented", payload["document_id"])


async def handle_upsert_graph(workspace_id: uuid.UUID, payload: dict) -> None:
    """Upsert extracted entities/relations into Neo4j."""
    logger.info("UPSERT_GRAPH doc=%s – not yet implemented", payload["document_id"])


def register_all() -> None:
    register_handler("PROCESS_DOCUMENT", handle_process_document)
    register_handler("CHUNK_DOCUMENT", handle_chunk_document)
    register_handler("EMBED_CHUNKS", handle_embed_chunks)
    register_handler("EXTRACT_ENTITIES_RELATIONS", handle_extract_entities_relations)
    register_handler("UPSERT_GRAPH", handle_upsert_graph)
