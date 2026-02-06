"""Utilities for graph-aware chunk creation and serialization."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any


def _unique_list(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def entity_chunk_key(vault_id: str, entity_key: str) -> str:
    return f"entity:{vault_id}:{entity_key}"


def relation_chunk_key(vault_id: str, from_key: str, rel_type: str, to_key: str) -> str:
    rel_type = normalize_relation_type(rel_type)
    raw = f"{vault_id}|{from_key}|{rel_type}|{to_key}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()
    return f"relation:{vault_id}:{digest}"


def normalize_relation_type(rel_type: str) -> str:
    return rel_type.upper().replace(" ", "_")


def _format_attributes(attributes: dict[str, Any]) -> str:
    if not attributes:
        return ""
    parts = [f"{k}={v}" for k, v in attributes.items() if k]
    return "; ".join(parts)


def serialize_entity_chunk(entity: dict, entity_key: str, evidence_chunk_ids: list[str]) -> str:
    aliases = entity.get("aliases") or []
    description = entity.get("description") or ""
    attributes = entity.get("attributes") or {}
    attributes_str = _format_attributes(attributes)
    citations = ", ".join(evidence_chunk_ids)

    lines = [
        f"Entity: {entity.get('name', '')}",
        f"Type: {entity.get('type', '')}",
        f"Key: {entity_key}",
    ]
    if description:
        lines.append(f"Summary: {description}")
    if aliases:
        lines.append(f"Aliases: {', '.join(aliases)}")
    if attributes_str:
        lines.append(f"Attributes: {attributes_str}")
    if citations:
        lines.append(f"Citations: {citations}")

    return "\n".join(lines)


def serialize_relation_chunk(relation: dict, from_key: str, to_key: str, evidence_chunk_ids: list[str]) -> str:
    rel_type = normalize_relation_type(relation.get("type", "RELATED_TO"))
    qualifiers = relation.get("qualifiers") or {}
    time_q = qualifiers.get("time") or ""
    location_q = qualifiers.get("location") or ""
    confidence_q = qualifiers.get("confidence")
    confidence_str = "" if confidence_q is None else str(confidence_q)
    citations = ", ".join(evidence_chunk_ids)

    lines = [
        f"Relation: {relation.get('from_name', '')} --{rel_type}--> {relation.get('to_name', '')}",
        f"FromKey: {from_key}",
        f"ToKey: {to_key}",
    ]
    qual_parts = []
    if time_q:
        qual_parts.append(f"time={time_q}")
    if location_q:
        qual_parts.append(f"location={location_q}")
    if confidence_str:
        qual_parts.append(f"confidence={confidence_str}")
    if qual_parts:
        lines.append(f"Qualifiers: {', '.join(qual_parts)}")
    evidence = relation.get("evidence", "")
    if evidence:
        lines.append(f"Evidence: {evidence}")
    if citations:
        lines.append(f"Citations: {citations}")

    return "\n".join(lines)


def merge_entity_metadata(existing: dict | None, new_data: dict, source_document_id: str) -> dict:
    existing = existing or {}

    aliases = _unique_list((existing.get("aliases") or []) + (new_data.get("aliases") or []))
    evidence_texts = _unique_list((existing.get("evidence_texts") or []) + (new_data.get("evidence_texts") or []))
    evidence_chunk_ids = _unique_list((existing.get("evidence_chunk_ids") or []) + (new_data.get("evidence_chunk_ids") or []))
    source_document_ids = _unique_list((existing.get("source_document_ids") or []) + [source_document_id])

    attributes = existing.get("attributes") or {}
    new_attributes = new_data.get("attributes") or {}
    history = existing.get("attributes_history") or []
    for key, value in new_attributes.items():
        if attributes.get(key) != value:
            history.append({
                "key": key,
                "value": value,
                "document_id": source_document_id,
                "observed_at": datetime.utcnow().isoformat(),
            })
    attributes.update(new_attributes)

    description = existing.get("description") or new_data.get("description") or ""

    return {
        "entity_key": new_data.get("entity_key") or existing.get("entity_key"),
        "entity_type": new_data.get("entity_type") or existing.get("entity_type"),
        "entity_name": new_data.get("entity_name") or existing.get("entity_name"),
        "aliases": aliases,
        "description": description,
        "attributes": attributes,
        "attributes_history": history,
        "evidence_texts": evidence_texts,
        "evidence_chunk_ids": evidence_chunk_ids,
        "source_document_ids": source_document_ids,
    }


def merge_relation_metadata(existing: dict | None, new_data: dict, source_document_id: str) -> dict:
    existing = existing or {}

    evidence_texts = _unique_list((existing.get("evidence_texts") or []) + (new_data.get("evidence_texts") or []))
    evidence_chunk_ids = _unique_list((existing.get("evidence_chunk_ids") or []) + (new_data.get("evidence_chunk_ids") or []))
    source_document_ids = _unique_list((existing.get("source_document_ids") or []) + [source_document_id])

    qualifiers = existing.get("qualifiers") or {}
    new_qualifiers = new_data.get("qualifiers") or {}
    history = existing.get("qualifiers_history") or []
    for key, value in new_qualifiers.items():
        if qualifiers.get(key) != value and value not in (None, ""):
            history.append({
                "key": key,
                "value": value,
                "document_id": source_document_id,
                "observed_at": datetime.utcnow().isoformat(),
            })
    qualifiers.update({k: v for k, v in new_qualifiers.items() if v not in (None, "")})

    return {
        "relation_type": new_data.get("relation_type") or existing.get("relation_type"),
        "from_key": new_data.get("from_key") or existing.get("from_key"),
        "to_key": new_data.get("to_key") or existing.get("to_key"),
        "from_name": new_data.get("from_name") or existing.get("from_name"),
        "to_name": new_data.get("to_name") or existing.get("to_name"),
        "qualifiers": qualifiers,
        "qualifiers_history": history,
        "evidence_texts": evidence_texts,
        "evidence_chunk_ids": evidence_chunk_ids,
        "source_document_ids": source_document_ids,
    }


def build_entity_metadata(entity: dict, entity_key: str, evidence_chunk_ids: list[str], source_document_id: str) -> dict:
    return {
        "entity_key": entity_key,
        "entity_type": entity.get("type", ""),
        "entity_name": entity.get("name", ""),
        "aliases": entity.get("aliases") or [],
        "description": entity.get("description") or "",
        "attributes": entity.get("attributes") or {},
        "attributes_history": [],
        "evidence_texts": [entity.get("evidence", "")] if entity.get("evidence") else [],
        "evidence_chunk_ids": evidence_chunk_ids,
        "source_document_ids": [source_document_id],
    }


def build_relation_metadata(relation: dict, from_key: str, to_key: str, evidence_chunk_ids: list[str], source_document_id: str) -> dict:
    qualifiers = relation.get("qualifiers") or {}
    return {
        "relation_type": normalize_relation_type(relation.get("type", "RELATED_TO")),
        "from_key": from_key,
        "to_key": to_key,
        "from_name": relation.get("from_name", ""),
        "to_name": relation.get("to_name", ""),
        "qualifiers": qualifiers,
        "qualifiers_history": [],
        "evidence_texts": [relation.get("evidence", "")] if relation.get("evidence") else [],
        "evidence_chunk_ids": evidence_chunk_ids,
        "source_document_ids": [source_document_id],
    }
