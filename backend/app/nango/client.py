"""Nango API client – fetches synced records and proxies provider APIs."""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

NANGO_BASE = "https://api.nango.dev"


def _headers(connection_id: str, provider_config_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.nango_secret_key}",
        "Connection-Id": connection_id,
        "Provider-Config-Key": provider_config_key,
    }


async def list_records(
    connection_id: str,
    provider_config_key: str,
    model: str,
    modified_after: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Fetch all synced records from Nango, paginating via cursor."""
    all_records: list[dict[str, Any]] = []
    cursor: str | None = None

    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            params: dict[str, Any] = {"model": model, "limit": limit}
            if modified_after:
                params["modified_after"] = modified_after
            if cursor:
                params["cursor"] = cursor

            url = f"{NANGO_BASE}/records"
            hdrs = _headers(connection_id, provider_config_key)
            logger.info("GET %s params=%s provider=%s connection=%s", url, params, provider_config_key, connection_id)

            resp = await client.get(url, headers=hdrs, params=params)
            logger.info("Nango response status=%d body_preview=%s", resp.status_code, resp.text[:500])
            resp.raise_for_status()
            body = resp.json()

            records = body.get("records", [])
            all_records.extend(records)
            logger.info("Fetched %d records (total so far: %d)", len(records), len(all_records))

            next_cursor = body.get("next_cursor")
            if not next_cursor or len(records) < limit:
                break
            cursor = next_cursor

    return all_records


async def fetch_notion_page_blocks(
    connection_id: str,
    page_id: str,
) -> list[dict[str, Any]]:
    """
    Fetch all block children of a Notion page via Nango proxy.
    Paginates through all blocks and returns the flat list.
    """
    all_blocks: list[dict[str, Any]] = []
    cursor: str | None = None

    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            params: dict[str, str] = {"page_size": "100"}
            if cursor:
                params["start_cursor"] = cursor

            resp = await client.get(
                f"{NANGO_BASE}/proxy/v1/blocks/{page_id}/children",
                headers=_headers(connection_id, "notion"),
                params=params,
            )
            resp.raise_for_status()
            body = resp.json()

            blocks = body.get("results", [])
            all_blocks.extend(blocks)

            if not body.get("has_more"):
                break
            cursor = body.get("next_cursor")

    return all_blocks


def extract_text_from_blocks(blocks: list[dict[str, Any]]) -> str:
    """Extract plain text from Notion block objects."""
    lines: list[str] = []
    for block in blocks:
        block_type = block.get("type", "")
        type_data = block.get(block_type, {})

        # Most text blocks have a "rich_text" array
        rich_text = type_data.get("rich_text", [])
        if rich_text:
            text = "".join(rt.get("plain_text", "") for rt in rich_text)
            if text.strip():
                lines.append(text)
            continue

        # Title blocks (child_page, child_database)
        title = type_data.get("title")
        if title:
            lines.append(title)

        # Caption on images/embeds
        caption = type_data.get("caption", [])
        if caption:
            text = "".join(rt.get("plain_text", "") for rt in caption)
            if text.strip():
                lines.append(text)

    return "\n".join(lines)
