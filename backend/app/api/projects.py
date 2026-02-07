"""Project CRUD API and Project Graph endpoints.

Phase 16: Project Graph Layer - Isolated graph for reasoning and exploration.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import delete, insert, select, update

from app.db import get_async_session
from app.models import (
    ContextVault,
    Project,
    ProjectStatus,
    ProjectVaultAssociation,
)
from app.processing.project_graph import (
    delete_prj_node,
    delete_project_graph,
    get_project_graph,
    write_prj_edge,
    write_prj_node,
    create_ukl_reference,
)
from app.processing.project_sync import (
    get_sync_log,
    get_sync_preview,
    sync_prj_edges_to_ukl,
    sync_prj_nodes_to_ukl,
)

router = APIRouter(prefix="/v1/projects", tags=["projects"])


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class ProjectCreate(BaseModel):
    workspace_id: uuid.UUID
    name: str
    description: str | None = None
    vault_ids: list[uuid.UUID] = []


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    vault_ids: list[uuid.UUID] | None = None
    status: str | None = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    status: str
    vault_ids: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Graph Pydantic Models
# ---------------------------------------------------------------------------


class GraphNodeCreate(BaseModel):
    key: str = "auto"  # "auto" to generate, otherwise use provided key
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


class GraphUpdateRequest(BaseModel):
    message_id: uuid.UUID | None = None
    nodes: list[GraphNodeCreate] = []
    edges: list[GraphEdgeCreate] = []
    ukl_refs: list[UklRefCreate] = []


class GraphUpdateResponse(BaseModel):
    nodes_created: int
    edges_created: int
    refs_created: int
    node_keys: list[str]


class GraphNodeOut(BaseModel):
    key: str
    node_type: str
    name: str
    properties: dict
    ukl_ref: str | None
    status: str | None
    source_message_id: str | None
    synced_to_ukl: bool
    created_at: str | None
    updated_at: str | None


class GraphEdgeOut(BaseModel):
    from_key: str
    to_key: str
    rel_type: str
    properties: dict
    source_message_id: str | None
    created_at: str | None


class ProjectGraphOut(BaseModel):
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]


# ---------------------------------------------------------------------------
# Sync Pydantic Models
# ---------------------------------------------------------------------------


class SyncRequest(BaseModel):
    node_keys: list[str] = []
    edge_keys: list[str] = []
    synced_by: str | None = None


class SyncResultItem(BaseModel):
    prj_key: str | None = None
    edge_key: str | None = None
    ukl_key: str | None = None
    action: str


class SyncResponse(BaseModel):
    node_results: list[SyncResultItem]
    edge_results: list[SyncResultItem]
    sync_log_id: str | None = None


class SyncPreviewNode(BaseModel):
    prj_key: str
    name: str | None = None
    node_type: str | None = None
    target_ukl_key: str | None = None
    target_ukl_label: str | None = None
    action: str
    existing_ukl_key: str | None = None
    existing_ukl_name: str | None = None


class SyncPreviewEdge(BaseModel):
    edge_key: str
    from_name: str | None = None
    to_name: str | None = None
    rel_type: str | None = None
    action: str
    from_synced: bool | None = None
    to_synced: bool | None = None
    from_ukl_key: str | None = None
    to_ukl_key: str | None = None


class SyncPreviewResponse(BaseModel):
    nodes: list[SyncPreviewNode]
    edges: list[SyncPreviewEdge]


class SyncLogEntry(BaseModel):
    id: str
    project_id: str
    synced_node_keys: list[str] | None
    synced_edge_keys: list[str] | None
    ukl_entity_keys: list[str] | None
    synced_by: str | None
    created_at: str


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


async def _get_vault_ids_for_project(session, project_id: uuid.UUID) -> list[uuid.UUID]:
    """Get all vault IDs associated with a project."""
    result = await session.execute(
        select(ProjectVaultAssociation.vault_id).where(
            ProjectVaultAssociation.project_id == project_id
        )
    )
    return [row[0] for row in result.fetchall()]


async def _set_vault_ids_for_project(
    session, project_id: uuid.UUID, workspace_id: uuid.UUID, vault_ids: list[uuid.UUID]
) -> None:
    """Set the vault IDs for a project (replaces existing)."""
    # Verify all vaults belong to the same workspace
    if vault_ids:
        result = await session.execute(
            select(ContextVault.id).where(
                ContextVault.id.in_(vault_ids),
                ContextVault.workspace_id == workspace_id,
            )
        )
        valid_ids = {row[0] for row in result.fetchall()}
        invalid_ids = set(vault_ids) - valid_ids
        if invalid_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Vaults not found or not in workspace: {invalid_ids}",
            )

    # Delete existing associations
    await session.execute(
        delete(ProjectVaultAssociation).where(
            ProjectVaultAssociation.project_id == project_id
        )
    )

    # Insert new associations
    for vault_id in vault_ids:
        await session.execute(
            insert(ProjectVaultAssociation).values(
                project_id=project_id,
                vault_id=vault_id,
            )
        )


# ---------------------------------------------------------------------------
# Project CRUD Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(body: ProjectCreate):
    """Create a new project with optional vault associations."""
    Session = get_async_session()
    project_id = uuid.uuid4()

    async with Session() as session:
        # Create project
        await session.execute(
            insert(Project).values(
                id=project_id,
                workspace_id=body.workspace_id,
                name=body.name,
                description=body.description,
                status=ProjectStatus.active,
            )
        )

        # Set vault associations
        if body.vault_ids:
            await _set_vault_ids_for_project(
                session, project_id, body.workspace_id, body.vault_ids
            )

        await session.commit()

        # Fetch created project
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one()
        vault_ids = await _get_vault_ids_for_project(session, project_id)

    return ProjectOut(
        id=project.id,
        workspace_id=project.workspace_id,
        name=project.name,
        description=project.description,
        status=project.status.value,
        vault_ids=vault_ids,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    workspace_id: uuid.UUID = Query(..., description="Filter by workspace"),
    status: str | None = Query(None, description="Filter by status (active, archived)"),
):
    """List all projects in a workspace."""
    Session = get_async_session()

    async with Session() as session:
        query = select(Project).where(Project.workspace_id == workspace_id)
        if status:
            query = query.where(Project.status == status)
        query = query.order_by(Project.created_at.desc())

        result = await session.execute(query)
        projects = result.scalars().all()

        # Get vault IDs for each project
        out = []
        for p in projects:
            vault_ids = await _get_vault_ids_for_project(session, p.id)
            out.append(
                ProjectOut(
                    id=p.id,
                    workspace_id=p.workspace_id,
                    name=p.name,
                    description=p.description,
                    status=p.status.value,
                    vault_ids=vault_ids,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
            )

    return out


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: uuid.UUID):
    """Get a single project by ID."""
    Session = get_async_session()

    async with Session() as session:
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        vault_ids = await _get_vault_ids_for_project(session, project_id)

    return ProjectOut(
        id=project.id,
        workspace_id=project.workspace_id,
        name=project.name,
        description=project.description,
        status=project.status.value,
        vault_ids=vault_ids,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: uuid.UUID, body: ProjectUpdate):
    """Update a project."""
    Session = get_async_session()

    async with Session() as session:
        # Fetch existing project
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Build updates
        updates = {}
        if body.name is not None:
            updates["name"] = body.name
        if body.description is not None:
            updates["description"] = body.description
        if body.status is not None:
            updates["status"] = body.status

        # Apply updates
        if updates:
            await session.execute(
                update(Project).where(Project.id == project_id).values(**updates)
            )

        # Update vault associations if provided
        if body.vault_ids is not None:
            await _set_vault_ids_for_project(
                session, project_id, project.workspace_id, body.vault_ids
            )

        await session.commit()

        # Fetch updated project
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one()
        vault_ids = await _get_vault_ids_for_project(session, project_id)

    return ProjectOut(
        id=project.id,
        workspace_id=project.workspace_id,
        name=project.name,
        description=project.description,
        status=project.status.value,
        vault_ids=vault_ids,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: uuid.UUID):
    """Delete a project and its associated data.

    This will also clean up:
    - Vault associations
    - Chat sessions and messages (TODO)
    - PRJ_Node/PRJ_REL in Neo4j (TODO)
    """
    Session = get_async_session()

    async with Session() as session:
        # Check if project exists
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Delete vault associations
        await session.execute(
            delete(ProjectVaultAssociation).where(
                ProjectVaultAssociation.project_id == project_id
            )
        )

        # Delete project
        await session.execute(delete(Project).where(Project.id == project_id))

        await session.commit()

    # Clean up Neo4j PRJ_Node/PRJ_REL for this project
    await delete_project_graph(project.workspace_id, project_id)

    return None


# ---------------------------------------------------------------------------
# Project Graph Endpoints
# ---------------------------------------------------------------------------


@router.get("/{project_id}/graph", response_model=ProjectGraphOut)
async def get_graph(project_id: uuid.UUID):
    """Get the project graph for UI visualization."""
    Session = get_async_session()

    async with Session() as session:
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    graph = await get_project_graph(project.workspace_id, project_id)

    return ProjectGraphOut(
        nodes=[GraphNodeOut(**n) for n in graph["nodes"]],
        edges=[GraphEdgeOut(**e) for e in graph["edges"]],
    )


@router.post("/{project_id}/graph/update", response_model=GraphUpdateResponse)
async def update_graph(project_id: uuid.UUID, body: GraphUpdateRequest):
    """Update the project graph with new nodes and edges.

    This is the primary endpoint for adding data to the project graph,
    typically called after processing a chat message.
    """
    Session = get_async_session()

    async with Session() as session:
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    workspace_id = project.workspace_id
    node_keys = []

    # Create/update nodes
    for node in body.nodes:
        key = await write_prj_node(
            workspace_id=workspace_id,
            project_id=project_id,
            key=node.key,
            node_type=node.node_type,
            name=node.name,
            properties=node.properties,
            ukl_ref=node.ukl_ref,
            source_message_id=body.message_id,
        )
        node_keys.append(key)

    # Create/update edges
    for edge in body.edges:
        await write_prj_edge(
            workspace_id=workspace_id,
            project_id=project_id,
            from_key=edge.from_key,
            to_key=edge.to_key,
            rel_type=edge.rel_type,
            properties=edge.properties,
            source_message_id=body.message_id,
        )

    # Create UKL references
    for ref in body.ukl_refs:
        await create_ukl_reference(
            workspace_id=workspace_id,
            project_id=project_id,
            prj_key=ref.prj_key,
            ukl_key=ref.ukl_key,
            ref_type=ref.ref_type,
        )

    return GraphUpdateResponse(
        nodes_created=len(body.nodes),
        edges_created=len(body.edges),
        refs_created=len(body.ukl_refs),
        node_keys=node_keys,
    )


@router.delete("/{project_id}/graph/nodes/{node_key:path}", status_code=204)
async def delete_graph_node(project_id: uuid.UUID, node_key: str):
    """Delete a node from the project graph."""
    Session = get_async_session()

    async with Session() as session:
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    deleted = await delete_prj_node(project.workspace_id, project_id, node_key)

    if not deleted:
        raise HTTPException(status_code=404, detail="Node not found")

    return None


# ---------------------------------------------------------------------------
# Sync Endpoints
# ---------------------------------------------------------------------------


@router.post("/{project_id}/sync", response_model=SyncResponse)
async def sync_to_ukl(project_id: uuid.UUID, body: SyncRequest):
    """Sync selected PRJ nodes and edges to UKL.

    This is the explicit sync operation that promotes project graph
    insights back to the Unified Knowledge Layer.

    GUARDRAIL: Only adds to UKL, never overwrites existing data.
    """
    Session = get_async_session()

    async with Session() as session:
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    workspace_id = project.workspace_id
    node_results = []
    edge_results = []
    sync_log_id = None

    # Sync nodes first
    if body.node_keys:
        node_sync = await sync_prj_nodes_to_ukl(
            workspace_id=workspace_id,
            project_id=project_id,
            node_keys=body.node_keys,
            synced_by=body.synced_by,
        )
        node_results = [
            SyncResultItem(prj_key=r["prj_key"], ukl_key=r.get("ukl_key"), action=r["action"])
            for r in node_sync["results"]
        ]
        sync_log_id = node_sync["sync_log_id"]

    # Sync edges (requires endpoints to be synced first)
    if body.edge_keys:
        edge_sync = await sync_prj_edges_to_ukl(
            workspace_id=workspace_id,
            project_id=project_id,
            edge_keys=body.edge_keys,
            synced_by=body.synced_by,
        )
        edge_results = [
            SyncResultItem(edge_key=r["edge_key"], action=r["action"])
            for r in edge_sync["results"]
        ]
        if not sync_log_id:
            sync_log_id = edge_sync["sync_log_id"]

    return SyncResponse(
        node_results=node_results,
        edge_results=edge_results,
        sync_log_id=sync_log_id,
    )


@router.post("/{project_id}/sync/preview", response_model=SyncPreviewResponse)
async def preview_sync(project_id: uuid.UUID, body: SyncRequest):
    """Preview what would be synced without actually syncing.

    Returns details about each node/edge and what action would be taken.
    """
    Session = get_async_session()

    async with Session() as session:
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    preview = await get_sync_preview(
        workspace_id=project.workspace_id,
        project_id=project_id,
        node_keys=body.node_keys,
        edge_keys=body.edge_keys,
    )

    return SyncPreviewResponse(
        nodes=[SyncPreviewNode(**n) for n in preview["nodes"]],
        edges=[SyncPreviewEdge(**e) for e in preview["edges"]],
    )


@router.get("/{project_id}/sync/log", response_model=list[SyncLogEntry])
async def get_project_sync_log(project_id: uuid.UUID, limit: int = 50):
    """Get sync log entries for a project."""
    Session = get_async_session()

    async with Session() as session:
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    logs = await get_sync_log(
        workspace_id=project.workspace_id,
        project_id=project_id,
        limit=limit,
    )

    return [SyncLogEntry(**log) for log in logs]
