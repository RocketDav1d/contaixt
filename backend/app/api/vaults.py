"""
Context Vault CRUD endpoints.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import delete, func, insert, select, update

from app.db import get_async_session
from app.models import ContextVault, Document

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

        result = await session.execute(
            select(ContextVault).where(ContextVault.id == vault_id)
        )
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
            select(ContextVault)
            .where(ContextVault.workspace_id == workspace_id)
            .order_by(ContextVault.created_at)
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
        result = await session.execute(
            select(ContextVault).where(ContextVault.id == vault_id)
        )
        vault = result.scalar_one_or_none()
        if not vault:
            raise HTTPException(status_code=404, detail="Vault not found")

        updates = {}
        if body.name is not None:
            updates["name"] = body.name
        if body.description is not None:
            updates["description"] = body.description

        if updates:
            await session.execute(
                update(ContextVault).where(ContextVault.id == vault_id).values(**updates)
            )
            await session.commit()

        result = await session.execute(
            select(ContextVault).where(ContextVault.id == vault_id)
        )
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
        result = await session.execute(
            select(ContextVault).where(ContextVault.id == vault_id)
        )
        vault = result.scalar_one_or_none()
        if not vault:
            raise HTTPException(status_code=404, detail="Vault not found")

        if vault.is_default:
            raise HTTPException(status_code=400, detail="Cannot delete the default vault")

        # Check if vault contains documents
        doc_count = await session.execute(
            select(func.count()).select_from(Document).where(Document.vault_id == vault_id)
        )
        if doc_count.scalar_one() > 0:
            raise HTTPException(status_code=400, detail="Cannot delete vault that contains documents")

        await session.execute(
            delete(ContextVault).where(ContextVault.id == vault_id)
        )
        await session.commit()
