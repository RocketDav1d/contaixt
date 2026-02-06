"""
Source connection registry + backfill trigger.

Connections are workspace-level. Vaults select which connections to include
via the vault_source_connections join table.
"""

import logging
import uuid

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import insert, select

from app.config import settings
from app.db import get_async_session
from app.api.ingest import IngestDocumentRequest, ingest_document
from app.models import ContextVault, SourceConnection, SourceType, VaultSourceConnection
from app.nango.client import list_records
from app.nango.content import fetch_notion_content_map
from app.nango.normalizers import NORMALIZERS, normalize_notion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/sources", tags=["sources"])

NANGO_API_URL = "https://api.nango.dev"

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


# =============================================================================
# Nango Connect Session
# =============================================================================


class ConnectSessionRequest(BaseModel):
    workspace_id: uuid.UUID
    user_id: str  # Unique identifier for the end user
    user_email: str | None = None
    user_display_name: str | None = None


class ConnectSessionResponse(BaseModel):
    token: str
    expires_at: str


@router.post("/nango/connect-session", response_model=ConnectSessionResponse)
async def create_connect_session(body: ConnectSessionRequest):
    """
    Create a Nango connect session for the frontend OAuth flow.

    The frontend uses this token to open Nango's Connect UI, which handles
    the OAuth flow and creates the connection. Nango sends a webhook when
    the connection is complete.
    """
    if not settings.nango_secret_key:
        raise HTTPException(500, "Nango secret key not configured")

    # Prepare request to Nango
    nango_body = {
        "end_user": {
            "id": body.user_id,
        },
        # Only include integrations we support
        "allowed_integrations": ["google-mail", "notion"],
    }

    if body.user_email:
        nango_body["end_user"]["email"] = body.user_email
    if body.user_display_name:
        nango_body["end_user"]["display_name"] = body.user_display_name

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NANGO_API_URL}/connect/sessions",
            headers={
                "Authorization": f"Bearer {settings.nango_secret_key}",
                "Content-Type": "application/json",
            },
            json=nango_body,
        )

    if response.status_code != 201:
        logger.error("Nango connect session failed: %s %s", response.status_code, response.text)
        raise HTTPException(500, f"Failed to create Nango session: {response.text}")

    data = response.json()["data"]
    return ConnectSessionResponse(
        token=data["token"],
        expires_at=data["expires_at"],
    )


# =============================================================================
# Vault helpers
# =============================================================================


async def _get_default_vault(workspace_id: uuid.UUID) -> uuid.UUID:
    """Get the default vault ID for a workspace."""
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(ContextVault.id).where(
                ContextVault.workspace_id == workspace_id,
                ContextVault.is_default == True,
            )
        )
        vault_id = result.scalar_one_or_none()
        if not vault_id:
            raise HTTPException(404, "No default vault found for workspace")
        return vault_id


async def _get_vault_ids_for_connection(connection_id: uuid.UUID) -> list[uuid.UUID]:
    """Get all vault IDs assigned to a connection."""
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(VaultSourceConnection.vault_id).where(
                VaultSourceConnection.source_connection_id == connection_id
            )
        )
        return [row[0] for row in result.fetchall()]


class RegisterConnectionRequest(BaseModel):
    workspace_id: uuid.UUID
    source_type: SourceType
    nango_connection_id: str
    external_account_id: str | None = None


class RegisterConnectionResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    source_type: SourceType
    nango_connection_id: str
    vault_ids: list[uuid.UUID]  # Vaults this connection is assigned to


@router.post("/nango/register", response_model=RegisterConnectionResponse, status_code=201)
async def register_connection(body: RegisterConnectionRequest):
    """Register a new OAuth connection and auto-assign to default vault."""
    default_vault_id = await _get_default_vault(body.workspace_id)

    Session = get_async_session()
    conn_id = uuid.uuid4()
    async with Session() as session:
        # Create the connection (workspace-level, no vault_id)
        await session.execute(
            insert(SourceConnection).values(
                id=conn_id,
                workspace_id=body.workspace_id,
                source_type=body.source_type,
                nango_connection_id=body.nango_connection_id,
                external_account_id=body.external_account_id,
            )
        )

        # Auto-assign to default vault
        await session.execute(
            insert(VaultSourceConnection).values(
                vault_id=default_vault_id,
                source_connection_id=conn_id,
            )
        )

        await session.commit()

    return RegisterConnectionResponse(
        id=conn_id,
        workspace_id=body.workspace_id,
        source_type=body.source_type,
        nango_connection_id=body.nango_connection_id,
        vault_ids=[default_vault_id],
    )


@router.get("")
async def list_sources(workspace_id: uuid.UUID):
    """List all source connections for a workspace with their vault assignments."""
    Session = get_async_session()
    async with Session() as session:
        # Get all connections
        result = await session.execute(
            select(SourceConnection).where(SourceConnection.workspace_id == workspace_id)
        )
        connections = result.scalars().all()

        # Get vault assignments for all connections
        conn_ids = [c.id for c in connections]
        if conn_ids:
            vault_result = await session.execute(
                select(
                    VaultSourceConnection.source_connection_id,
                    VaultSourceConnection.vault_id
                ).where(VaultSourceConnection.source_connection_id.in_(conn_ids))
            )
            vault_rows = vault_result.fetchall()
        else:
            vault_rows = []

    # Group vault_ids by connection
    vault_map: dict[uuid.UUID, list[uuid.UUID]] = {}
    for row in vault_rows:
        conn_id, vault_id = row
        if conn_id not in vault_map:
            vault_map[conn_id] = []
        vault_map[conn_id].append(vault_id)

    return [
        {
            "id": str(r.id),
            "workspace_id": str(r.workspace_id),
            "source_type": r.source_type.value,
            "nango_connection_id": r.nango_connection_id,
            "external_account_id": r.external_account_id,
            "status": r.status.value if r.status else None,
            "vault_ids": [str(v) for v in vault_map.get(r.id, [])],
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in connections
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

    ingested = 0
    for doc in docs:
        if not doc.get("content_text"):
            continue
        await ingest_document(
            IngestDocumentRequest(
                workspace_id=workspace_id,
                source_connection_id=conn.id,
                **doc
            )
        )
        ingested += 1

    logger.info("Backfill: ingested %d documents", ingested)
    return BackfillResponse(fetched=len(records), ingested=ingested)
