"""
LLM-based entity and relation extraction.
Uses OpenAI with strict JSON output to extract Person, Company, Topic entities
and typed relations with qualifiers and evidence from document text.
"""

import json
import logging
import uuid

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an entity extraction system. Given a document, extract entities and relations.

Return ONLY valid JSON matching this schema:
{
  "entities": [
    {
      "type": "Person|Company|Topic",
      "name": "...",
      "email": "...",
      "domain": "...",
      "aliases": ["..."],
      "description": "...",
      "attributes": {"key": "value"},
      "evidence": "..."
    }
  ],
  "relations": [
    {
      "from_name": "...",
      "to_name": "...",
      "type": "MENTIONS|WORKS_AT|HAS_CONTACT|RELATED_TO",
      "evidence": "...",
      "qualifiers": {"time": "...", "location": "...", "confidence": 0.0}
    }
  ]
}

Rules:
- type must be one of: Person, Company, Topic
- For Person: include email if available
- For Company: include domain if available (e.g. "acme.com")
- For Topic: use a short normalized label (2-4 words max)
- aliases should be short name variants (if present)
- description should be a short one-sentence summary (no speculation)
- attributes should be key facts found in the text (keep to 1-5 items)
- evidence must be a short span from the text (max 120 chars)
- qualifiers.time and qualifiers.location can be empty if not present
- qualifiers.confidence is 0–1 based on how explicit the relation is
- Only extract entities actually mentioned in the text
- If no entities found, return {"entities": [], "relations": []}
- Do NOT hallucinate entities not present in the text"""

USER_TEMPLATE = """Extract entities and relations from this document.

Title: {title}
Author: {author_name} <{author_email}>
Source: {source_type}

Content:
{content}"""


QUERY_SYSTEM_PROMPT = """You extract named entities from user queries.

Return ONLY valid JSON matching this schema:
{
  "entities": [
    {"name": "...", "type": "Person|Company|Topic|Unknown"}
  ]
}

Rules:
- Only include entities explicitly mentioned in the query.
- If type is unclear, use "Unknown".
- If no entities found, return {"entities": []}.
"""


async def extract_entities_relations(
    content_text: str,
    title: str = "",
    author_name: str = "",
    author_email: str = "",
    source_type: str = "",
) -> dict:
    """
    Extract entities and relations from text via LLM.
    Returns {"entities": [...], "relations": [...]}.
    """
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Truncate very long content to avoid token limits
    content = content_text[:8000] if len(content_text) > 8000 else content_text

    user_msg = USER_TEMPLATE.format(
        title=title or "(no title)",
        author_name=author_name or "unknown",
        author_email=author_email or "unknown",
        source_type=source_type or "unknown",
        content=content,
    )

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM JSON: %s", raw[:200])
        data = {"entities": [], "relations": []}

    # Normalize entity fields
    for ent in data.get("entities", []):
        if not isinstance(ent.get("aliases"), list):
            ent["aliases"] = []
        if not isinstance(ent.get("attributes"), dict):
            ent["attributes"] = {}
        if not isinstance(ent.get("description"), str):
            ent["description"] = ""
        if not isinstance(ent.get("evidence"), str):
            ent["evidence"] = ""

    # Normalize relation fields
    for rel in data.get("relations", []):
        if not isinstance(rel.get("evidence"), str):
            rel["evidence"] = ""
        qualifiers = rel.get("qualifiers")
        if not isinstance(qualifiers, dict):
            qualifiers = {}
        rel["qualifiers"] = qualifiers

    # Add heuristic entities from email headers
    heuristic = _heuristic_entities(author_name, author_email)
    existing_names = {e.get("name", "").lower() for e in data.get("entities", [])}
    for ent in heuristic:
        if ent["name"].lower() not in existing_names:
            data["entities"].append(ent)

    return data


async def extract_query_entities(query: str) -> list[dict]:
    """Extract entities from a user query."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": QUERY_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Failed to parse query entity JSON: %s", raw[:200])
        data = {"entities": []}

    return data.get("entities", [])


IGNORE_DOMAINS = {"gmail.com", "googlemail.com", "yahoo.com", "hotmail.com", "outlook.com", "gmx.de", "gmx.net", "web.de", "icloud.com", "me.com", "t-online.de", "live.com", "aol.com", "protonmail.com", "proton.me", "mail.com"}


def _heuristic_entities(author_name: str, author_email: str) -> list[dict]:
    """Extract Person + Company from email headers."""
    entities = []

    if author_email and "@" in author_email:
        entities.append({
            "type": "Person",
            "name": author_name or author_email.split("@")[0],
            "email": author_email,
            "aliases": [],
            "description": "",
            "attributes": {},
            "evidence": "",
        })
        domain = author_email.split("@")[1].lower()
        if domain not in IGNORE_DOMAINS:
            company_name = domain.split(".")[0].capitalize()
            entities.append({
                "type": "Company",
                "name": company_name,
                "domain": domain,
                "aliases": [],
                "description": "",
                "attributes": {},
                "evidence": "",
            })

    return entities
