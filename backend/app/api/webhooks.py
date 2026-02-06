"""
Nango webhook receiver.
Single endpoint handles all providers – routes by providerConfigKey.
"""

import hashlib
import hmac
import logging

from fastapi import APIRouter, Header, HTTPException, Request

from app.api.ingest import IngestDocumentRequest, ingest_document
from app.config import settings
from app.nango.client import list_records
from app.nango.content import fetch_notion_content_map
from app.nango.normalizers import NORMALIZERS, normalize_notion
from app.nango.sync import resolve_workspace_and_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])


def _verify_signature(payload: bytes, signature: str | None) -> bool:
    if not settings.nango_webhook_secret:
        return True  # skip verification if no secret configured
    if not signature:
        return False
    expected = hmac.HMAC(
        settings.nango_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/nango")
async def nango_webhook(
    request: Request,
    x_nango_hmac_sha256: str | None = Header(None),
):
    raw_body = await request.body()

    if not _verify_signature(raw_body, x_nango_hmac_sha256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    event_type = payload.get("type")

    if event_type != "sync":
        logger.info("Ignoring non-sync webhook: type=%s", event_type)
        return {"status": "ignored"}

    connection_id = payload.get("connectionId", "")
    provider_config_key = payload.get("providerConfigKey", "")
    model = payload.get("model", "")
    modified_after = payload.get("modifiedAfter")
    success = payload.get("success", False)

    if not success:
        logger.warning("Sync failed for connection=%s provider=%s", connection_id, provider_config_key)
        return {"status": "sync_failed"}

    logger.info(
        "Sync webhook: connection=%s provider=%s model=%s modified_after=%s",
        connection_id,
        provider_config_key,
        model,
        modified_after,
    )

    ws_id, source_connection_id = await resolve_workspace_and_connection(connection_id, provider_config_key)
    if not ws_id:
        logger.warning("No workspace found for nango connection=%s", connection_id)
        return {"status": "no_workspace"}

    if provider_config_key not in NORMALIZERS:
        logger.warning("No normalizer for provider=%s", provider_config_key)
        return {"status": "unsupported_provider"}

    records = await list_records(
        connection_id=connection_id,
        provider_config_key=provider_config_key,
        model=model,
        modified_after=modified_after,
    )
    logger.info("Fetched %d records from Nango", len(records))

    # Notion needs extra content fetch; Gmail has body inline
    if provider_config_key == "notion":
        content_map = await fetch_notion_content_map(connection_id, records)
        docs = normalize_notion(records, content_map=content_map)
    else:
        normalizer = NORMALIZERS[provider_config_key]
        docs = normalizer(records)

    ingested = 0
    for doc in docs:
        if not doc.get("content_text"):
            continue
        await ingest_document(
            IngestDocumentRequest(
                workspace_id=ws_id,
                source_connection_id=source_connection_id,
                **doc
            )
        )
        ingested += 1

    logger.info("Ingested %d documents for workspace=%s", ingested, ws_id)
    return {"status": "ok", "ingested": ingested}
