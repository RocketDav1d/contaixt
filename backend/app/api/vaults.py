"""
Context Vault CRUD endpoints.

Vaults select which connections' documents are searchable within them
via the vault_source_connections join table.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import delete, func, insert, select, update

from app.db import get_async_session
from app.models import ContextVault, Document, SourceConnection, VaultSourceConnection

router = APIRouter(prefix="/v1/vaults", tags=["vaults"])


class VaultCreate(BaseModel):
    workspace_id: uuid.UUID
    name: str
    description: str | None = None


class VaultUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class VaultOut(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    is_default: bool
    created_at: datetime


@router.post("", response_model=VaultOut, status_code=201)
async def create_vault(body: VaultCreate):
    Session = get_async_session()
    vault_id = uuid.uuid4()
    async with Session() as session:
        await session.execute(
            insert(ContextVault).values(
                id=vault_id,
                workspace_id=body.workspace_id,
                name=body.name,
                description=body.description,
                is_default=False,
            )
        )
        await session.commit()

        result = await session.execute(select(ContextVault).where(ContextVault.id == vault_id))
        vault = result.scalar_one()

    return VaultOut(
        id=vault.id,
        workspace_id=vault.workspace_id,
        name=vault.name,
        description=vault.description,
        is_default=vault.is_default,
        created_at=vault.created_at,
    )


@router.get("", response_model=list[VaultOut])
async def list_vaults(workspace_id: uuid.UUID = Query(...)):
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(ContextVault).where(ContextVault.workspace_id == workspace_id).order_by(ContextVault.created_at)
        )
        rows = result.scalars().all()

    return [
        VaultOut(
            id=r.id,
            workspace_id=r.workspace_id,
            name=r.name,
            description=r.description,
            is_default=r.is_default,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.patch("/{vault_id}", response_model=VaultOut)
async def update_vault(vault_id: uuid.UUID, body: VaultUpdate):
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(select(ContextVault).where(ContextVault.id == vault_id))
        vault = result.scalar_one_or_none()
        if not vault:
            raise HTTPException(status_code=404, detail="Vault not found")

        updates = {}
        if body.name is not None:
            updates["name"] = body.name
        if body.description is not None:
            updates["description"] = body.description

        if updates:
            await session.execute(update(ContextVault).where(ContextVault.id == vault_id).values(**updates))
            await session.commit()

        result = await session.execute(select(ContextVault).where(ContextVault.id == vault_id))
        vault = result.scalar_one()

    return VaultOut(
        id=vault.id,
        workspace_id=vault.workspace_id,
        name=vault.name,
        description=vault.description,
        is_default=vault.is_default,
        created_at=vault.created_at,
    )


@router.delete("/{vault_id}", status_code=204)
async def delete_vault(vault_id: uuid.UUID):
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(select(ContextVault).where(ContextVault.id == vault_id))
        vault = result.scalar_one_or_none()
        if not vault:
            raise HTTPException(status_code=404, detail="Vault not found")

        if vault.is_default:
            raise HTTPException(status_code=400, detail="Cannot delete the default vault")

        # Check if vault has documents via its assigned connections
        doc_count = await session.execute(
            select(func.count())
            .select_from(Document)
            .join(
                VaultSourceConnection,
                Document.source_connection_id == VaultSourceConnection.source_connection_id
            )
            .where(VaultSourceConnection.vault_id == vault_id)
        )
        if doc_count.scalar_one() > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete vault that has documents from assigned connections"
            )

        # Delete vault (CASCADE will remove vault_source_connections entries)
        await session.execute(
            delete(ContextVault).where(ContextVault.id == vault_id)
        )
        await session.commit()


# ---------------------------------------------------------------------------
# Connection Assignment Endpoints
# ---------------------------------------------------------------------------


class VaultConnectionsOut(BaseModel):
    vault_id: uuid.UUID
    connection_ids: list[uuid.UUID]


class UpdateVaultConnectionsRequest(BaseModel):
    connection_ids: list[uuid.UUID]


class ConnectionOut(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    source_type: str
    nango_connection_id: str
    external_account_id: str | None
    status: str | None


@router.get("/{vault_id}/connections", response_model=list[ConnectionOut])
async def get_vault_connections(vault_id: uuid.UUID):
    """Get all connections assigned to a vault."""
    Session = get_async_session()
    async with Session() as session:
        # Verify vault exists
        result = await session.execute(
            select(ContextVault).where(ContextVault.id == vault_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Vault not found")

        # Get connections via join table
        result = await session.execute(
            select(SourceConnection)
            .join(
                VaultSourceConnection,
                SourceConnection.id == VaultSourceConnection.source_connection_id
            )
            .where(VaultSourceConnection.vault_id == vault_id)
        )
        connections = result.scalars().all()

    return [
        ConnectionOut(
            id=c.id,
            workspace_id=c.workspace_id,
            source_type=c.source_type.value,
            nango_connection_id=c.nango_connection_id,
            external_account_id=c.external_account_id,
            status=c.status.value if c.status else None,
        )
        for c in connections
    ]


@router.put("/{vault_id}/connections", response_model=VaultConnectionsOut)
async def update_vault_connections(vault_id: uuid.UUID, body: UpdateVaultConnectionsRequest):
    """Replace all connection assignments for a vault."""
    Session = get_async_session()
    async with Session() as session:
        # Verify vault exists
        result = await session.execute(
            select(ContextVault).where(ContextVault.id == vault_id)
        )
        vault = result.scalar_one_or_none()
        if not vault:
            raise HTTPException(status_code=404, detail="Vault not found")

        # Verify all connection_ids belong to the same workspace
        if body.connection_ids:
            result = await session.execute(
                select(SourceConnection).where(SourceConnection.id.in_(body.connection_ids))
            )
            connections = result.scalars().all()

            if len(connections) != len(body.connection_ids):
                raise HTTPException(status_code=400, detail="One or more connections not found")

            for conn in connections:
                if conn.workspace_id != vault.workspace_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Connection {conn.id} belongs to a different workspace"
                    )

        # Delete existing assignments for this vault
        await session.execute(
            delete(VaultSourceConnection).where(VaultSourceConnection.vault_id == vault_id)
        )

        # Insert new assignments
        for conn_id in body.connection_ids:
            await session.execute(
                insert(VaultSourceConnection).values(
                    vault_id=vault_id,
                    source_connection_id=conn_id,
                )
            )

        await session.commit()

    return VaultConnectionsOut(
        vault_id=vault_id,
        connection_ids=body.connection_ids,
    )
