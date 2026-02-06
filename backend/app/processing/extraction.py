"""
LLM-based entity and relation extraction.
Uses OpenAI with strict JSON output to extract Person, Company, Topic entities
and MENTIONS relations from document text.
"""

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an entity extraction system. Given a document, extract entities and relations.

Return ONLY valid JSON matching this schema:
{
  "entities": [
    {"type": "Person|Company|Topic", "name": "...", "email": "...", "domain": "..."}
  ],
  "relations": [
    {"from_name": "...", "to_name": "...", "type": "MENTIONS|WORKS_AT|HAS_CONTACT", "evidence": "..."}
  ]
}

Rules:
- type must be one of: Person, Company, Topic
- For Person: include email if available
- For Company: include domain if available (e.g. "acme.com")
- For Topic: use a short normalized label (2-4 words max)
- Only extract entities actually mentioned in the text
- Keep evidence spans short (max 100 chars)
- If no entities found, return {"entities": [], "relations": []}
- Do NOT hallucinate entities not present in the text"""

USER_TEMPLATE = """Extract entities and relations from this document.

Title: {title}
Author: {author_name} <{author_email}>
Source: {source_type}

Content:
{content}"""


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
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM JSON: %s", raw[:200])
        data = {"entities": [], "relations": []}

    # Add heuristic entities from email headers
    heuristic = _heuristic_entities(author_name, author_email)
    existing_names = {e.get("name", "").lower() for e in data.get("entities", [])}
    for ent in heuristic:
        if ent["name"].lower() not in existing_names:
            data["entities"].append(ent)

    return data


IGNORE_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "gmx.de",
    "gmx.net",
    "web.de",
    "icloud.com",
    "me.com",
    "t-online.de",
    "live.com",
    "aol.com",
    "protonmail.com",
    "proton.me",
    "mail.com",
}


def _heuristic_entities(author_name: str, author_email: str) -> list[dict]:
    """Extract Person + Company from email headers."""
    entities = []

    if author_email and "@" in author_email:
        entities.append(
            {
                "type": "Person",
                "name": author_name or author_email.split("@")[0],
                "email": author_email,
            }
        )
        domain = author_email.split("@")[1].lower()
        if domain not in IGNORE_DOMAINS:
            company_name = domain.split(".")[0].capitalize()
            entities.append(
                {
                    "type": "Company",
                    "name": company_name,
                    "domain": domain,
                }
            )

    return entities
