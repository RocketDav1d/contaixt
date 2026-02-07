"""Nango Proxy client for making authenticated API calls to external services.

The Nango Proxy automatically injects OAuth credentials for the connection,
allowing us to make API calls without managing tokens ourselves.

Proxy endpoint: https://api.nango.dev/proxy/{path}
Headers required:
- Authorization: Bearer <NANGO_SECRET_KEY>
- Connection-Id: <nango_connection_id>
- Provider-Config-Key: <provider_config_key>
"""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

NANGO_BASE = "https://api.nango.dev"
TIMEOUT = 60  # Longer timeout for file downloads


def _headers(connection_id: str, provider_config_key: str) -> dict[str, str]:
    """Build headers for Nango proxy requests."""
    return {
        "Authorization": f"Bearer {settings.nango_secret_key}",
        "Connection-Id": connection_id,
        "Provider-Config-Key": provider_config_key,
    }


async def proxy_get(
    connection_id: str,
    provider_config_key: str,
    endpoint: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make a GET request through Nango proxy, returning JSON response."""
    url = f"{NANGO_BASE}/proxy{endpoint}"
    headers = _headers(connection_id, provider_config_key)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        logger.info("Proxy GET %s provider=%s connection=%s", endpoint, provider_config_key, connection_id)
        resp = await client.get(url, headers=headers, params=params or {})
        resp.raise_for_status()
        return resp.json()


async def proxy_get_binary(
    connection_id: str,
    provider_config_key: str,
    endpoint: str,
    params: dict[str, Any] | None = None,
) -> bytes:
    """Make a GET request through Nango proxy, returning binary content."""
    url = f"{NANGO_BASE}/proxy{endpoint}"
    headers = _headers(connection_id, provider_config_key)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        logger.info("Proxy GET (binary) %s provider=%s connection=%s", endpoint, provider_config_key, connection_id)
        resp = await client.get(url, headers=headers, params=params or {})
        resp.raise_for_status()
        return resp.content


# =============================================================================
# Google Drive specific helpers
# =============================================================================


async def drive_list_files(
    connection_id: str,
    page_size: int = 100,
    page_token: str | None = None,
    query: str | None = None,
) -> dict[str, Any]:
    """List files in Google Drive.

    Args:
        connection_id: Nango connection ID
        page_size: Number of files per page (max 1000)
        page_token: Token for pagination
        query: Drive search query (e.g., "mimeType='application/pdf'")

    Returns:
        Dict with 'files' list and optional 'nextPageToken'
    """
    params: dict[str, Any] = {
        "pageSize": page_size,
        "fields": "nextPageToken,files(id,name,mimeType,modifiedTime,webViewLink,size,parents)",
    }
    if page_token:
        params["pageToken"] = page_token
    if query:
        params["q"] = query

    return await proxy_get(
        connection_id=connection_id,
        provider_config_key="google-drive",
        endpoint="/drive/v3/files",
        params=params,
    )


async def drive_list_supported_files(connection_id: str) -> list[dict[str, Any]]:
    """List all supported files from Google Drive with pagination.

    Queries for file types we can extract text from:
    - Google Docs, Sheets, Slides
    - PDFs
    - Office documents (DOCX, XLSX, PPTX)
    - Plain text files
    """
    supported_query = " or ".join([
        "mimeType='application/vnd.google-apps.document'",
        "mimeType='application/vnd.google-apps.spreadsheet'",
        "mimeType='application/vnd.google-apps.presentation'",
        "mimeType='application/pdf'",
        "mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'",
        "mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'",
        "mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation'",
        "mimeType='text/plain'",
        "mimeType='text/csv'",
        "mimeType='text/markdown'",
    ])

    all_files: list[dict[str, Any]] = []
    page_token: str | None = None

    while True:
        response = await drive_list_files(
            connection_id=connection_id,
            page_size=100,
            page_token=page_token,
            query=supported_query,
        )
        files = response.get("files", [])
        all_files.extend(files)

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    logger.info("Listed %d supported files from Google Drive", len(all_files))
    return all_files


async def drive_get_file_metadata(
    connection_id: str,
    file_id: str,
) -> dict[str, Any]:
    """Get metadata for a specific file."""
    params = {
        "fields": "id,name,mimeType,modifiedTime,webViewLink,size,parents,owners,createdTime",
    }
    return await proxy_get(
        connection_id=connection_id,
        provider_config_key="google-drive",
        endpoint=f"/drive/v3/files/{file_id}",
        params=params,
    )


async def drive_download_file(
    connection_id: str,
    file_id: str,
) -> bytes:
    """Download file content (for binary files like PDF, DOCX, etc.)."""
    return await proxy_get_binary(
        connection_id=connection_id,
        provider_config_key="google-drive",
        endpoint=f"/drive/v3/files/{file_id}",
        params={"alt": "media"},
    )


async def drive_export_file(
    connection_id: str,
    file_id: str,
    mime_type: str,
) -> bytes:
    """Export a Google Workspace file (Docs, Sheets, Slides) to specified format.

    Args:
        connection_id: Nango connection ID
        file_id: Google Drive file ID
        mime_type: Target format:
            - 'text/plain' for Google Docs
            - 'text/csv' for Google Sheets
            - 'text/plain' for Google Slides

    Returns:
        Exported content as bytes
    """
    return await proxy_get_binary(
        connection_id=connection_id,
        provider_config_key="google-drive",
        endpoint=f"/drive/v3/files/{file_id}/export",
        params={"mimeType": mime_type},
    )


# MIME type constants for Google Workspace files
GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
GOOGLE_SHEET_MIME = "application/vnd.google-apps.spreadsheet"
GOOGLE_SLIDES_MIME = "application/vnd.google-apps.presentation"
GOOGLE_FOLDER_MIME = "application/vnd.google-apps.folder"

# Supported file types for content extraction
SUPPORTED_MIME_TYPES = {
    # Google Workspace (export via API)
    GOOGLE_DOC_MIME,
    GOOGLE_SHEET_MIME,
    GOOGLE_SLIDES_MIME,
    # Binary files (download and parse)
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
    # Plain text
    "text/plain",
    "text/csv",
    "text/markdown",
}


def is_supported_file(mime_type: str) -> bool:
    """Check if we can extract content from this file type."""
    return mime_type in SUPPORTED_MIME_TYPES
