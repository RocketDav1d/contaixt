"""
Fetch actual page content for Notion pages via Nango proxy.
Notion's content-metadata sync only returns metadata — this fills in the body text.
"""

import logging
from typing import Any

from app.nango.client import extract_text_from_blocks, fetch_notion_page_blocks

logger = logging.getLogger(__name__)


async def fetch_notion_content_map(
    connection_id: str,
    records: list[dict[str, Any]],
) -> dict[str, str]:
    """
    For each Notion page record, fetch block children and extract plain text.
    Returns {page_id: plain_text_content}.
    """
    content_map: dict[str, str] = {}

    pages = [r for r in records if r.get("type") == "page"]
    logger.info("Fetching content for %d Notion pages", len(pages))

    for page in pages:
        page_id = page.get("id", "")
        if not page_id:
            continue
        try:
            blocks = await fetch_notion_page_blocks(connection_id, page_id)
            text = extract_text_from_blocks(blocks)
            if text.strip():
                content_map[page_id] = text
                logger.debug("Page %s: extracted %d chars", page_id, len(text))
        except Exception:
            logger.warning("Failed to fetch blocks for page %s", page_id, exc_info=True)

    logger.info("Fetched content for %d/%d pages", len(content_map), len(pages))
    return content_map
