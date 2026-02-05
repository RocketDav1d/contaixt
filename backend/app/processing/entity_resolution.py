"""
Entity resolution: generates stable, deduplicated keys for entities.

Key strategy:
  Person:  person:email:<email>       (if email known)
  Company: company:domain:<domain>    (if domain known)
  Topic:   topic:<normalized_label>
  Fallback: <type>:name:<normalized_name>
"""

import re
import unicodedata


def _normalize(s: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\s+", " ", s.lower().strip())
    return s


def resolve_entity_key(entity: dict) -> str:
    """Generate a stable key for an entity dict."""
    etype = entity.get("type", "unknown").lower()
    name = entity.get("name", "")
    email = entity.get("email", "")
    domain = entity.get("domain", "")

    if etype == "person" and email:
        return f"person:email:{email.lower().strip()}"

    if etype == "company" and domain:
        return f"company:domain:{domain.lower().strip()}"

    if etype == "topic":
        return f"topic:{_normalize(name)}"

    return f"{etype}:name:{_normalize(name)}"
