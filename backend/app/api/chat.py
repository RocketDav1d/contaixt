"""Chat Sessions and Messages API.

Phase 16: Project Graph Layer - Chat endpoints for project-scoped conversations.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, insert, select

from app.db import get_async_session
from app.models import (
    ChatMessage,
    ChatRole,
    ChatSession,
    Project,
)
from app.processing.project_graph import (
    create_ukl_reference,
    write_prj_edge,
    write_prj_node,
)

router = APIRouter(prefix="/v1/projects/{project_id}/chat", tags=["chat"])


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class ChatSessionCreate(BaseModel):
    title: str | None = None


class ChatSessionOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    workspace_id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class GraphNodeCreate(BaseModel):
    key: str = "auto"
    node_type: str
    name: str
    properties: dict = {}
    ukl_ref: str | None = None


class GraphEdgeCreate(BaseModel):
    from_key: str
    to_key: str
    rel_type: str
    properties: dict = {}


class UklRefCreate(BaseModel):
    prj_key: str
    ukl_key: str
    ref_type: str = "references"


class GraphDelta(BaseModel):
    nodes: list[GraphNodeCreate] = []
    edges: list[GraphEdgeCreate] = []
    ukl_refs: list[UklRefCreate] = []


class ChatMessageCreate(BaseModel):
    role: str  # user, assistant, system
    content: str
    context_vault_ids_used: list[uuid.UUID] | None = None
    graph_delta: GraphDelta | None = None


class ChatMessageOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    context_vault_ids_used: list[uuid.UUID] | None
    graph_nodes_created: int
    graph_edges_created: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


async def _get_project(session, project_id: uuid.UUID) -> Project:
    """Get project and verify it exists."""
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _get_session(session, session_id: uuid.UUID, project_id: uuid.UUID) -> ChatSession:
    """Get chat session and verify it exists and belongs to project."""
    result = await session.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.project_id == project_id,
        )
    )
    chat_session = result.scalar_one_or_none()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return chat_session


# ---------------------------------------------------------------------------
# Chat Session Endpoints
# ---------------------------------------------------------------------------


@router.post("/sessions", response_model=ChatSessionOut, status_code=201)
async def create_session(project_id: uuid.UUID, body: ChatSessionCreate):
    """Create a new chat session in a project."""
    Session = get_async_session()
    session_id = uuid.uuid4()

    async with Session() as session:
        project = await _get_project(session, project_id)

        await session.execute(
            insert(ChatSession).values(
                id=session_id,
                project_id=project_id,
                workspace_id=project.workspace_id,
                title=body.title,
            )
        )
        await session.commit()

        result = await session.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        chat_session = result.scalar_one()

    return ChatSessionOut(
        id=chat_session.id,
        project_id=chat_session.project_id,
        workspace_id=chat_session.workspace_id,
        title=chat_session.title,
        created_at=chat_session.created_at,
        updated_at=chat_session.updated_at,
    )


@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_sessions(project_id: uuid.UUID):
    """List all chat sessions in a project."""
    Session = get_async_session()

    async with Session() as session:
        await _get_project(session, project_id)

        result = await session.execute(
            select(ChatSession)
            .where(ChatSession.project_id == project_id)
            .order_by(ChatSession.created_at.desc())
        )
        sessions = result.scalars().all()

    return [
        ChatSessionOut(
            id=s.id,
            project_id=s.project_id,
            workspace_id=s.workspace_id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
async def get_session(project_id: uuid.UUID, session_id: uuid.UUID):
    """Get a single chat session."""
    Session = get_async_session()

    async with Session() as session:
        chat_session = await _get_session(session, session_id, project_id)

    return ChatSessionOut(
        id=chat_session.id,
        project_id=chat_session.project_id,
        workspace_id=chat_session.workspace_id,
        title=chat_session.title,
        created_at=chat_session.created_at,
        updated_at=chat_session.updated_at,
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(project_id: uuid.UUID, session_id: uuid.UUID):
    """Delete a chat session and all its messages."""
    Session = get_async_session()

    async with Session() as session:
        await _get_session(session, session_id, project_id)

        # Delete messages first
        await session.execute(
            delete(ChatMessage).where(ChatMessage.session_id == session_id)
        )

        # Delete session
        await session.execute(
            delete(ChatSession).where(ChatSession.id == session_id)
        )

        await session.commit()

    return None


# ---------------------------------------------------------------------------
# Chat Message Endpoints
# ---------------------------------------------------------------------------


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageOut, status_code=201)
async def create_message(
    project_id: uuid.UUID,
    session_id: uuid.UUID,
    body: ChatMessageCreate,
):
    """Create a new chat message in a session.

    If graph_delta is provided, the corresponding PRJ nodes/edges will be
    created in the project graph.
    """
    Session = get_async_session()
    message_id = uuid.uuid4()

    async with Session() as session:
        chat_session = await _get_session(session, session_id, project_id)
        workspace_id = chat_session.workspace_id

        # Validate role
        try:
            role = ChatRole(body.role)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role: {body.role}. Must be one of: user, assistant, system",
            )

        # Prepare graph delta JSON for storage
        graph_delta_json = None
        nodes_created = 0
        edges_created = 0

        if body.graph_delta:
            graph_delta_json = {
                "nodes": [n.model_dump() for n in body.graph_delta.nodes],
                "edges": [e.model_dump() for e in body.graph_delta.edges],
                "ukl_refs": [r.model_dump() for r in body.graph_delta.ukl_refs],
            }

            # Create PRJ nodes
            for node in body.graph_delta.nodes:
                await write_prj_node(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    key=node.key,
                    node_type=node.node_type,
                    name=node.name,
                    properties=node.properties,
                    ukl_ref=node.ukl_ref,
                    source_message_id=message_id,
                )
                nodes_created += 1

            # Create PRJ edges
            for edge in body.graph_delta.edges:
                await write_prj_edge(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    from_key=edge.from_key,
                    to_key=edge.to_key,
                    rel_type=edge.rel_type,
                    properties=edge.properties,
                    source_message_id=message_id,
                )
                edges_created += 1

            # Create UKL references
            for ref in body.graph_delta.ukl_refs:
                await create_ukl_reference(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    prj_key=ref.prj_key,
                    ukl_key=ref.ukl_key,
                    ref_type=ref.ref_type,
                )

        # Store message
        await session.execute(
            insert(ChatMessage).values(
                id=message_id,
                session_id=session_id,
                workspace_id=workspace_id,
                role=role,
                content=body.content,
                context_vault_ids_used=[str(v) for v in body.context_vault_ids_used]
                if body.context_vault_ids_used
                else None,
                graph_delta_json=graph_delta_json,
            )
        )
        await session.commit()

        result = await session.execute(
            select(ChatMessage).where(ChatMessage.id == message_id)
        )
        message = result.scalar_one()

    return ChatMessageOut(
        id=message.id,
        session_id=message.session_id,
        role=message.role.value,
        content=message.content,
        context_vault_ids_used=[uuid.UUID(v) for v in message.context_vault_ids_used]
        if message.context_vault_ids_used
        else None,
        graph_nodes_created=nodes_created,
        graph_edges_created=edges_created,
        created_at=message.created_at,
    )


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
async def list_messages(project_id: uuid.UUID, session_id: uuid.UUID):
    """List all messages in a chat session."""
    Session = get_async_session()

    async with Session() as session:
        await _get_session(session, session_id, project_id)

        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = result.scalars().all()

    return [
        ChatMessageOut(
            id=m.id,
            session_id=m.session_id,
            role=m.role.value,
            content=m.content,
            context_vault_ids_used=[uuid.UUID(v) for v in m.context_vault_ids_used]
            if m.context_vault_ids_used
            else None,
            graph_nodes_created=len(m.graph_delta_json.get("nodes", []))
            if m.graph_delta_json
            else 0,
            graph_edges_created=len(m.graph_delta_json.get("edges", []))
            if m.graph_delta_json
            else 0,
            created_at=m.created_at,
        )
        for m in messages
    ]
