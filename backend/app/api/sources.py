"""
Source connection registry + backfill trigger.
"""

import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import insert, select

from app.db import get_async_session
from app.api.ingest import IngestDocumentRequest, _resolve_default_vault, ingest_document
from app.models import SourceConnection, SourceType
from app.nango.client import list_records
from app.nango.content import fetch_notion_content_map
from app.nango.normalizers import NORMALIZERS, normalize_notion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/sources", tags=["sources"])

# Map our source_type → Nango providerConfigKey
SOURCE_TO_PROVIDER = {
    "gmail": "google-mail",
    "notion": "notion",
}

# Nango sync model names per provider
DEFAULT_MODELS = {
    "google-mail": "GmailEmail",
    "notion": "ContentMetadata",
}


class RegisterConnectionRequest(BaseModel):
    workspace_id: uuid.UUID
    vault_id: uuid.UUID | None = None  # None = use default vault
    source_type: SourceType
    nango_connection_id: str
    external_account_id: str | None = None


class RegisterConnectionResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    vault_id: uuid.UUID
    source_type: SourceType
    nango_connection_id: str


@router.post("/nango/register", response_model=RegisterConnectionResponse, status_code=201)
async def register_connection(body: RegisterConnectionRequest):
    vault_id = body.vault_id or await _resolve_default_vault(body.workspace_id)
    Session = get_async_session()
    conn_id = uuid.uuid4()
    async with Session() as session:
        await session.execute(
            insert(SourceConnection).values(
                id=conn_id,
                workspace_id=body.workspace_id,
                vault_id=vault_id,
                source_type=body.source_type,
                nango_connection_id=body.nango_connection_id,
                external_account_id=body.external_account_id,
            )
        )
        await session.commit()
    return RegisterConnectionResponse(
        id=conn_id,
        workspace_id=body.workspace_id,
        vault_id=vault_id,
        source_type=body.source_type,
        nango_connection_id=body.nango_connection_id,
    )


@router.get("")
async def list_sources(workspace_id: uuid.UUID):
    """List all source connections for a workspace."""
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(SourceConnection).where(SourceConnection.workspace_id == workspace_id)
        )
        rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "workspace_id": str(r.workspace_id),
            "vault_id": str(r.vault_id),
            "source_type": r.source_type.value,
            "nango_connection_id": r.nango_connection_id,
            "external_account_id": r.external_account_id,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]


@router.get("/nango/connections")
async def list_connections(workspace_id: uuid.UUID):
    """Legacy endpoint - use GET /v1/sources instead."""
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(SourceConnection).where(SourceConnection.workspace_id == workspace_id)
        )
        rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "source_type": r.source_type,
            "nango_connection_id": r.nango_connection_id,
            "status": r.status,
        }
        for r in rows
    ]


class BackfillResponse(BaseModel):
    fetched: int
    ingested: int


@router.post("/{source_type}/backfill", response_model=BackfillResponse)
async def backfill(source_type: SourceType, workspace_id: uuid.UUID):
    """
    Fetch all existing records from Nango for a source and ingest them.
    Pass workspace_id as query param.
    """
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(SourceConnection).where(
                SourceConnection.workspace_id == workspace_id,
                SourceConnection.source_type == source_type,
            )
        )
        conn = result.scalars().first()

    if not conn:
        raise HTTPException(404, f"No {source_type.value} connection found for workspace")

    provider_key = SOURCE_TO_PROVIDER.get(source_type.value, source_type.value)
    model = DEFAULT_MODELS.get(provider_key, "records")

    if provider_key not in NORMALIZERS:
        raise HTTPException(400, f"No normalizer for provider {provider_key}")

    # Fetch all records (no modified_after = full backfill)
    records = await list_records(
        connection_id=conn.nango_connection_id,
        provider_config_key=provider_key,
        model=model,
    )
    logger.info("Backfill: fetched %d records from Nango for %s", len(records), source_type.value)

    # Notion needs extra content fetch; Gmail has body inline
    if provider_key == "notion":
        content_map = await fetch_notion_content_map(conn.nango_connection_id, records)
        docs = normalize_notion(records, content_map=content_map)
    else:
        normalizer = NORMALIZERS[provider_key]
        docs = normalizer(records)

    vault_id = conn.vault_id

    ingested = 0
    for doc in docs:
        if not doc.get("content_text"):
            continue
        await ingest_document(IngestDocumentRequest(workspace_id=workspace_id, vault_id=vault_id, **doc))
        ingested += 1

    logger.info("Backfill: ingested %d documents", ingested)
    return BackfillResponse(fetched=len(records), ingested=ingested)
