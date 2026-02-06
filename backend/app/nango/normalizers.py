"""
Normalizers: transform Nango provider records into our IngestDocumentRequest format.

Nango model schemas (from integration-templates source):

GmailEmail:
  id, sender, recipients, date, subject, body, attachments, threadId

ContentMetadata (Notion):
  id, path, type, last_modified, title, parent_id
  NOTE: No body text — content must be fetched separately via blocks API.
"""

import logging
import re
from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.nango.proxy import GOOGLE_FOLDER_MIME, SUPPORTED_MIME_TYPES

logger = logging.getLogger(__name__)

# Normalizer: (records, ...) -> list of ingest-ready dicts
NormalizerFn = Callable[..., list[dict[str, Any]]]


def _strip_html(html: str) -> str:
    """Minimal HTML tag stripping."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_gmail(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Map Nango GmailEmail records → ingest-ready dicts.
    Fields: id, sender, recipients, date, subject, body, attachments, threadId
    """
    docs = []
    for rec in records:
        sender = rec.get("sender") or ""
        sender_name = ""
        sender_email = sender
        match = re.match(r"^(.+?)\s*<(.+?)>$", sender)
        if match:
            sender_name = match.group(1).strip().strip('"')
            sender_email = match.group(2).strip()

        body = rec.get("body") or ""
        if "<" in body and ">" in body:
            body = _strip_html(body)

        external_id = rec.get("id") or ""
        thread_id = rec.get("threadId") or ""
        subject = rec.get("subject") or "(no subject)"
        date_str = rec.get("date")

        created_at = None
        if date_str:
            try:
                created_at = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        docs.append(
            {
                "source_type": "gmail",
                "external_id": external_id,
                "url": f"https://mail.google.com/mail/u/0/#inbox/{thread_id}" if thread_id else None,
                "title": subject,
                "author_name": sender_name,
                "author_email": sender_email,
                "created_at": created_at,
                "content_text": body,
            }
        )
    return docs


def normalize_notion(records: list[dict[str, Any]], content_map: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """
    Map Nango ContentMetadata records → ingest-ready dicts.
    Fields: id, path, type, last_modified, title, parent_id

    content_map: optional {page_id: plain_text} with pre-fetched page content.
    If not provided, content_text will be the title only (metadata-only mode).
    """
    content_map = content_map or {}
    docs = []
    for rec in records:
        # Skip databases, only ingest pages
        if rec.get("type") == "database":
            continue

        external_id = rec.get("id") or ""
        url = rec.get("path") or ""
        title = rec.get("title") or "(untitled)"

        content = content_map.get(external_id, "")

        updated_at = None
        last_modified = rec.get("last_modified")
        if last_modified:
            try:
                updated_at = datetime.fromisoformat(str(last_modified).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        docs.append(
            {
                "source_type": "notion",
                "external_id": external_id,
                "url": url,
                "title": title,
                "author_name": None,
                "author_email": None,
                "created_at": updated_at,
                "content_text": content if content else title,
            }
        )
    return docs


def normalize_google_drive(records: list[dict[str, Any]], content_map: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """
    Map Nango Google Drive file records → ingest-ready dicts.

    Google Drive syncs metadata only. Content must be fetched separately
    via the Drive API (export for Google Workspace files, download for binaries).

    content_map: optional {file_id: plain_text} with pre-fetched file content.
    If not provided, content_text will be empty (metadata-only mode for async processing).
    """
    content_map = content_map or {}
    docs = []

    for rec in records:
        mime_type = rec.get("mimeType") or ""

        # Skip folders
        if mime_type == GOOGLE_FOLDER_MIME:
            continue

        # Skip unsupported file types
        if mime_type not in SUPPORTED_MIME_TYPES:
            logger.debug("Skipping unsupported file type: %s (%s)", rec.get("name"), mime_type)
            continue

        external_id = rec.get("id") or ""
        name = rec.get("name") or "(untitled)"
        web_link = rec.get("webViewLink") or ""

        content = content_map.get(external_id, "")

        modified_time = None
        modified_str = rec.get("modifiedTime")
        if modified_str:
            try:
                modified_time = datetime.fromisoformat(str(modified_str).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # Extract owner info if available
        owners = rec.get("owners") or []
        owner_name = None
        owner_email = None
        if owners:
            owner_name = owners[0].get("displayName")
            owner_email = owners[0].get("emailAddress")

        docs.append({
            "source_type": "google-drive",
            "external_id": external_id,
            "url": web_link,
            "title": name,
            "author_name": owner_name,
            "author_email": owner_email,
            "created_at": modified_time,
            "content_text": content,  # Empty for async processing, populated for sync
        })

    return docs


NORMALIZERS: dict[str, NormalizerFn] = {
    "google-mail": normalize_gmail,
    "gmail": normalize_gmail,
    "notion": normalize_notion,
    "google-drive": normalize_google_drive,
}
