import uuid

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import insert, select

from app.db import get_async_session
from app.models import ContextVault, Workspace

router = APIRouter(prefix="/v1/workspaces", tags=["workspaces"])


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceOut(BaseModel):
    id: uuid.UUID
    name: str


@router.post("", response_model=WorkspaceOut, status_code=201)
async def create_workspace(body: WorkspaceCreate):
    Session = get_async_session()
    ws_id = uuid.uuid4()
    async with Session() as session:
        await session.execute(insert(Workspace).values(id=ws_id, name=body.name))
        # Auto-create Default vault
        await session.execute(
            insert(ContextVault).values(
                id=uuid.uuid4(),
                workspace_id=ws_id,
                name="Default",
                is_default=True,
            )
        )
        await session.commit()
    return WorkspaceOut(id=ws_id, name=body.name)


@router.get("", response_model=list[WorkspaceOut])
async def list_workspaces():
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(select(Workspace))
        rows = result.scalars().all()
    return [WorkspaceOut(id=r.id, name=r.name) for r in rows]
