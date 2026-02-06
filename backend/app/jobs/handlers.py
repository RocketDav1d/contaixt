"""
Job type handlers. Each handler receives (workspace_id, payload_json).
"""

import json
import logging
import time
import uuid

from sqlalchemy import delete, func, insert, select

from app.db import get_async_session
from app.jobs.runner import register_handler
from app.models import ChunkType, Document, DocumentChunk, EntityMention, Job, JobStatus, JobType

logger = logging.getLogger(__name__)


async def _has_pending_job(workspace_id: uuid.UUID, job_type: JobType, document_id: str) -> bool:
    """Check if a queued/running job already exists for this document + type."""
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(func.count()).select_from(Job).where(
                Job.workspace_id == workspace_id,
                Job.type == job_type,
                Job.status.in_([JobStatus.queued, JobStatus.running]),
                Job.payload_json["document_id"].as_string() == document_id,
            )
        )
        return result.scalar_one() > 0


async def handle_process_document(workspace_id: uuid.UUID, payload: dict) -> None:
    """Fan-out: enqueue CHUNK_DOCUMENT (which will enqueue embedding + extraction)."""
    from app.jobs.enqueue import enqueue_job

    document_id = payload["document_id"]
    logger.info("PROCESS_DOCUMENT doc=%s", document_id)

    # Idempotency: skip if job already queued for this document
    if not await _has_pending_job(workspace_id, JobType.CHUNK_DOCUMENT, document_id):
        await enqueue_job(workspace_id, JobType.CHUNK_DOCUMENT, {"document_id": document_id})
    else:
        logger.info("PROCESS_DOCUMENT: skipping CHUNK_DOCUMENT (already queued) doc=%s", document_id)


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
                    vault_id=doc.vault_id,
                    document_id=document_id,
                    idx=ch.idx,
                    chunk_type=ChunkType.evidence,
                    chunk_key=f"evidence:{document_id}:{ch.idx}",
                    text=ch.text,
                    start_offset=ch.start_offset,
                    end_offset=ch.end_offset,
                    metadata_json={"role": "evidence"},
                )
            )
        await session.commit()

    logger.info("CHUNK_DOCUMENT: stored %d chunks for doc=%s", len(chunks), document_id)

    # Enqueue embedding + extraction after chunks exist
    if not await _has_pending_job(workspace_id, JobType.EMBED_CHUNKS, str(document_id)):
        await enqueue_job(workspace_id, JobType.EMBED_CHUNKS, {"document_id": str(document_id)})
    if not await _has_pending_job(workspace_id, JobType.EXTRACT_ENTITIES_RELATIONS, str(document_id)):
        await enqueue_job(workspace_id, JobType.EXTRACT_ENTITIES_RELATIONS, {"document_id": str(document_id)})


async def handle_embed_chunks(workspace_id: uuid.UUID, payload: dict) -> None:
    """Embed chunks via OpenAI and store vectors in pgvector."""
    from app.processing.embeddings import embed_and_store

    document_id = uuid.UUID(payload["document_id"])
    chunk_ids = payload.get("chunk_ids")
    logger.info("EMBED_CHUNKS doc=%s", document_id)

    parsed_chunk_ids = [uuid.UUID(cid) for cid in chunk_ids] if chunk_ids else None
    force = bool(parsed_chunk_ids)
    count = await embed_and_store(workspace_id, document_id, chunk_ids=parsed_chunk_ids, force=force)
    logger.info("EMBED_CHUNKS: embedded %d chunks for doc=%s", count, document_id)


async def handle_extract_entities_relations(workspace_id: uuid.UUID, payload: dict) -> None:
    """LLM extraction of entities + relations, entity resolution, store mentions, enqueue graph upsert."""
    from app.jobs.enqueue import enqueue_job
    from app.processing.entity_resolution import resolve_entity_key
    from app.processing.extraction import extract_entities_relations

    document_id = uuid.UUID(payload["document_id"])
    logger.info("EXTRACT_ENTITIES_RELATIONS doc=%s", document_id)

    Session = get_async_session()

    def _find_evidence_chunks(chunks: list[DocumentChunk], evidence: str, fallback_terms: list[str] | None = None) -> list[uuid.UUID]:
        if not chunks:
            return []
        matches: list[uuid.UUID] = []
        if evidence and evidence.strip():
            needle = evidence.strip().lower()
            for ch in chunks:
                if needle in ch.text.lower():
                    matches.append(ch.id)
        if not matches and fallback_terms:
            lowered = [t.lower() for t in fallback_terms if t]
            for ch in chunks:
                hay = ch.text.lower()
                if any(term in hay for term in lowered):
                    matches.append(ch.id)
        return list(dict.fromkeys(matches))

    # Fetch document + evidence chunks
    async with Session() as session:
        result = await session.execute(
            select(Document).where(
                Document.id == document_id,
                Document.workspace_id == workspace_id,
            )
        )
        doc = result.scalar_one_or_none()
        chunk_result = await session.execute(
            select(DocumentChunk).where(
                DocumentChunk.workspace_id == workspace_id,
                DocumentChunk.document_id == document_id,
                DocumentChunk.chunk_type == ChunkType.evidence,
            ).order_by(DocumentChunk.idx)
        )
        evidence_chunks = list(chunk_result.scalars().all())

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

    # Resolve entity keys + attach evidence chunk ids
    entity_keys = {}
    for ent in entities:
        key = resolve_entity_key(ent)
        entity_keys[ent.get("name", "")] = key
        evidence_chunk_ids = _find_evidence_chunks(
            evidence_chunks,
            ent.get("evidence", ""),
            fallback_terms=[ent.get("name", "")],
        )
        ent["entity_key"] = key
        ent["evidence_chunk_ids"] = [str(cid) for cid in evidence_chunk_ids]

    # Attach relation keys + evidence chunk ids
    for rel in relations:
        from_name = rel.get("from_name", "")
        to_name = rel.get("to_name", "")
        rel["from_key"] = entity_keys.get(from_name, "")
        rel["to_key"] = entity_keys.get(to_name, "")
        evidence_chunk_ids = _find_evidence_chunks(
            evidence_chunks,
            rel.get("evidence", ""),
            fallback_terms=[from_name, to_name],
        )
        rel["evidence_chunk_ids"] = [str(cid) for cid in evidence_chunk_ids]

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
            chunk_id = ent.get("evidence_chunk_ids", [])
            await session.execute(
                insert(EntityMention).values(
                    id=uuid.uuid4(),
                    workspace_id=workspace_id,
                    vault_id=doc.vault_id,
                    document_id=document_id,
                    chunk_id=uuid.UUID(chunk_id[0]) if chunk_id else None,
                    entity_key=entity_keys.get(name, ""),
                    entity_type=ent.get("type", "unknown"),
                    entity_name=name,
                    confidence=1.0,
                )
            )
        await session.commit()

    logger.info(
        "EXTRACT: %d entities, %d relations for doc=%s",
        len(entities), len(relations), document_id,
    )

    # Enqueue graph upsert with extracted data
    await enqueue_job(
        workspace_id,
        JobType.UPSERT_GRAPH,
        {
            "document_id": str(document_id),
            "vault_id": str(doc.vault_id),
            "entities": entities,
            "relations": relations,
            "entity_keys": entity_keys,
        },
    )


async def handle_upsert_graph(workspace_id: uuid.UUID, payload: dict) -> None:
    """Upsert extracted entities/relations into Neo4j."""
    from app.jobs.enqueue import enqueue_job
    from app.processing.graph import upsert_entities_and_relations
    from app.processing.graph_chunks import (
        build_entity_metadata,
        build_relation_metadata,
        entity_chunk_key,
        merge_entity_metadata,
        merge_relation_metadata,
        relation_chunk_key,
        serialize_entity_chunk,
        serialize_relation_chunk,
    )

    document_id = uuid.UUID(payload["document_id"])
    vault_id = uuid.UUID(payload["vault_id"]) if payload.get("vault_id") else None
    entities = payload.get("entities", [])
    relations = payload.get("relations", [])
    entity_keys = payload.get("entity_keys", {})

    logger.info("UPSERT_GRAPH doc=%s (%d entities, %d relations)", document_id, len(entities), len(relations))

    await upsert_entities_and_relations(
        workspace_id=workspace_id,
        vault_id=vault_id,
        document_id=document_id,
        entities=entities,
        relations=relations,
        entity_keys=entity_keys,
    )

    # Upsert entity/relation chunks for vector retrieval
    if vault_id:
        chunk_ids_to_embed: list[str] = []
        Session = get_async_session()
        vault_id_str = str(vault_id)
        doc_id_str = str(document_id)

        entity_keys_list = []
        relation_keys_list = []
        for ent in entities:
            key = ent.get("entity_key") or entity_keys.get(ent.get("name", ""))
            if key:
                entity_keys_list.append(entity_chunk_key(vault_id_str, key))
        for rel in relations:
            from_key = rel.get("from_key") or entity_keys.get(rel.get("from_name", ""))
            to_key = rel.get("to_key") or entity_keys.get(rel.get("to_name", ""))
            if from_key and to_key:
                rel_type = rel.get("type", "RELATED_TO")
                relation_keys_list.append(relation_chunk_key(vault_id_str, from_key, rel_type, to_key))

        all_keys = list(dict.fromkeys(entity_keys_list + relation_keys_list))
        existing = {}

        async with Session() as session:
            if all_keys:
                result = await session.execute(
                    select(DocumentChunk).where(
                        DocumentChunk.workspace_id == workspace_id,
                        DocumentChunk.chunk_key.in_(all_keys),
                    )
                )
                existing = {c.chunk_key: c for c in result.scalars().all()}

            # Entities
            for ent in entities:
                key = ent.get("entity_key") or entity_keys.get(ent.get("name", ""))
                if not key:
                    continue
                ckey = entity_chunk_key(vault_id_str, key)
                evidence_chunk_ids = ent.get("evidence_chunk_ids", [])
                new_meta = build_entity_metadata(ent, key, evidence_chunk_ids, doc_id_str)
                existing_chunk = existing.get(ckey)
                if existing_chunk:
                    merged_meta = merge_entity_metadata(existing_chunk.metadata_json, new_meta, doc_id_str)
                    entity_for_text = {
                        "name": merged_meta.get("entity_name"),
                        "type": merged_meta.get("entity_type"),
                        "aliases": merged_meta.get("aliases"),
                        "description": merged_meta.get("description"),
                        "attributes": merged_meta.get("attributes"),
                    }
                    existing_chunk.text = serialize_entity_chunk(
                        entity_for_text,
                        key,
                        merged_meta.get("evidence_chunk_ids", []),
                    )
                    existing_chunk.metadata_json = merged_meta
                    chunk_ids_to_embed.append(str(existing_chunk.id))
                else:
                    text = serialize_entity_chunk(ent, key, evidence_chunk_ids)
                    new_chunk_id = uuid.uuid4()
                    await session.execute(
                        insert(DocumentChunk).values(
                            id=new_chunk_id,
                            workspace_id=workspace_id,
                            vault_id=vault_id,
                            document_id=document_id,
                            idx=0,
                            chunk_type=ChunkType.entity,
                            chunk_key=ckey,
                            text=text,
                            start_offset=0,
                            end_offset=0,
                            metadata_json=new_meta,
                        )
                    )
                    chunk_ids_to_embed.append(str(new_chunk_id))

            # Relations
            for rel in relations:
                from_key = rel.get("from_key") or entity_keys.get(rel.get("from_name", ""))
                to_key = rel.get("to_key") or entity_keys.get(rel.get("to_name", ""))
                if not from_key or not to_key:
                    continue
                rel_type = rel.get("type", "RELATED_TO")
                ckey = relation_chunk_key(vault_id_str, from_key, rel_type, to_key)
                evidence_chunk_ids = rel.get("evidence_chunk_ids", [])
                new_meta = build_relation_metadata(rel, from_key, to_key, evidence_chunk_ids, doc_id_str)
                existing_chunk = existing.get(ckey)
                if existing_chunk:
                    merged_meta = merge_relation_metadata(existing_chunk.metadata_json, new_meta, doc_id_str)
                    relation_for_text = {
                        "from_name": merged_meta.get("from_name"),
                        "to_name": merged_meta.get("to_name"),
                        "type": merged_meta.get("relation_type"),
                        "evidence": (merged_meta.get("evidence_texts") or [""])[-1],
                        "qualifiers": merged_meta.get("qualifiers"),
                    }
                    existing_chunk.text = serialize_relation_chunk(
                        relation_for_text,
                        from_key,
                        to_key,
                        merged_meta.get("evidence_chunk_ids", []),
                    )
                    existing_chunk.metadata_json = merged_meta
                    chunk_ids_to_embed.append(str(existing_chunk.id))
                else:
                    text = serialize_relation_chunk(rel, from_key, to_key, evidence_chunk_ids)
                    new_chunk_id = uuid.uuid4()
                    await session.execute(
                        insert(DocumentChunk).values(
                            id=new_chunk_id,
                            workspace_id=workspace_id,
                            vault_id=vault_id,
                            document_id=document_id,
                            idx=0,
                            chunk_type=ChunkType.relation,
                            chunk_key=ckey,
                            text=text,
                            start_offset=0,
                            end_offset=0,
                            metadata_json=new_meta,
                        )
                    )
                    chunk_ids_to_embed.append(str(new_chunk_id))

            await session.commit()

        if chunk_ids_to_embed:
            chunk_ids_to_embed = list(dict.fromkeys(chunk_ids_to_embed))
            await enqueue_job(
                workspace_id,
                JobType.EMBED_CHUNKS,
                {"document_id": str(document_id), "chunk_ids": chunk_ids_to_embed},
            )

    logger.info("UPSERT_GRAPH: done for doc=%s", document_id)


def register_all() -> None:
    register_handler("PROCESS_DOCUMENT", handle_process_document)
    register_handler("CHUNK_DOCUMENT", handle_chunk_document)
    register_handler("EMBED_CHUNKS", handle_embed_chunks)
    register_handler("EXTRACT_ENTITIES_RELATIONS", handle_extract_entities_relations)
    register_handler("UPSERT_GRAPH", handle_upsert_graph)
