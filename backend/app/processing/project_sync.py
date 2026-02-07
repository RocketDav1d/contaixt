"""Project Graph to UKL Sync operations.

Phase 16: Project Graph Layer - Explicit sync from PRJ graph to UKL.

GUARDRAIL: This module syncs PRJ_Node data into UKL entities.
- Never overwrites existing UKL data (ON CREATE only)
- Creates SYNCED_AS edge for traceability
- Logs all syncs to PostgreSQL
"""

import json
import logging
import uuid

from sqlalchemy import insert

from app.db import get_async_session
from app.models import ProjectSyncLog
from app.neo4j_client import get_session
from app.processing.entity_resolution import resolve_entity_key


def _parse_properties(props):
    """Parse properties from JSON string or return as-is if dict."""
    if isinstance(props, str):
        return json.loads(props) if props else {}
    return props or {}

logger = logging.getLogger(__name__)

# Map PRJ node_type → Neo4j UKL label
LABEL_MAP = {
    "person": "Person",
    "company": "Company",
    "topic": "Topic",
}


async def sync_prj_nodes_to_ukl(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    node_keys: list[str],
    synced_by: str | None = None,
) -> dict:
    """
    Sync selected PRJ_Node entities to UKL.

    GUARDRAIL: Only adds to UKL, never overwrites existing data.

    Args:
        workspace_id: Tenant isolation
        project_id: Project scope
        node_keys: List of PRJ_Node keys to sync
        synced_by: User identifier for audit log

    Returns:
        {
            "results": [{"prj_key": ..., "ukl_key": ..., "action": ...}, ...],
            "sync_log_id": ...
        }
    """
    ws = str(workspace_id)
    pid = str(project_id)
    results = []
    ukl_entity_keys = []
    sync_log_id = uuid.uuid4()

    try:
        async with get_session() as session:
            for prj_key in node_keys:
                # 1. Fetch PRJ_Node
                result = await session.run(
                    """
                    MATCH (n:PRJ_Node {workspace_id: $ws, project_id: $pid, key: $key})
                    RETURN n.node_type AS node_type,
                           n.name AS name,
                           n.properties AS properties,
                           n.status AS status
                    """,
                    ws=ws,
                    pid=pid,
                    key=prj_key,
                )
                record = await result.single()

                if not record:
                    results.append({
                        "prj_key": prj_key,
                        "ukl_key": None,
                        "action": "not_found",
                    })
                    continue

                node_type = record["node_type"]
                name = record["name"]
                properties = _parse_properties(record["properties"])
                status = record["status"]

                # Skip if already synced
                if status == "synced":
                    results.append({
                        "prj_key": prj_key,
                        "ukl_key": None,
                        "action": "already_synced",
                    })
                    continue

                # 2. Build entity dict for resolution
                entity_dict = {
                    "type": node_type,
                    "name": name,
                    "email": properties.get("email"),
                    "domain": properties.get("domain"),
                }

                # 3. Resolve entity key
                ukl_key = resolve_entity_key(entity_dict)
                ukl_label = LABEL_MAP.get(node_type.lower(), "Topic")

                # 4. Check if UKL entity exists
                existing = await session.run(
                    f"""
                    MATCH (e:{ukl_label} {{workspace_id: $ws, key: $ukl_key}})
                    RETURN e.name AS name
                    """,
                    ws=ws,
                    ukl_key=ukl_key,
                )
                existing_record = await existing.single()
                action = "matched" if existing_record else "created"

                # 5. MERGE into UKL (only set properties ON CREATE)
                await session.run(
                    f"""
                    MERGE (e:{ukl_label} {{workspace_id: $ws, key: $ukl_key}})
                    ON CREATE SET e.name = $name,
                                  e.email = $email,
                                  e.domain = $domain,
                                  e.created_at = datetime()
                    """,
                    ws=ws,
                    ukl_key=ukl_key,
                    name=name,
                    email=properties.get("email", ""),
                    domain=properties.get("domain", ""),
                )

                # 6. Create SYNCED_AS edge for traceability
                await session.run(
                    f"""
                    MATCH (prj:PRJ_Node {{workspace_id: $ws, project_id: $pid, key: $prj_key}})
                    MATCH (ukl:{ukl_label} {{workspace_id: $ws, key: $ukl_key}})
                    MERGE (prj)-[r:SYNCED_AS]->(ukl)
                    SET r.synced_at = datetime(),
                        r.sync_log_id = $sync_log_id,
                        r.project_id = $pid
                    """,
                    ws=ws,
                    pid=pid,
                    prj_key=prj_key,
                    ukl_key=ukl_key,
                    sync_log_id=str(sync_log_id),
                )

                # 7. Update PRJ_Node status to 'synced'
                await session.run(
                    """
                    MATCH (n:PRJ_Node {workspace_id: $ws, project_id: $pid, key: $key})
                    SET n.status = 'synced',
                        n.updated_at = datetime()
                    """,
                    ws=ws,
                    pid=pid,
                    key=prj_key,
                )

                results.append({
                    "prj_key": prj_key,
                    "ukl_key": ukl_key,
                    "action": action,
                })
                ukl_entity_keys.append(ukl_key)

        # 8. Log sync in PostgreSQL
        Session = get_async_session()
        async with Session() as db_session:
            await db_session.execute(
                insert(ProjectSyncLog).values(
                    id=sync_log_id,
                    project_id=project_id,
                    workspace_id=workspace_id,
                    synced_node_keys=node_keys,
                    synced_edge_keys=[],
                    ukl_entity_keys=ukl_entity_keys,
                    synced_by=synced_by,
                )
            )
            await db_session.commit()

        logger.info(
            "Synced %d PRJ nodes to UKL (project=%s, sync_log=%s)",
            len(node_keys), project_id, sync_log_id
        )

    except Exception as e:
        logger.error("Failed to sync PRJ nodes to UKL: %s", e)
        raise

    return {
        "results": results,
        "sync_log_id": str(sync_log_id),
    }


async def sync_prj_edges_to_ukl(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    edge_keys: list[str],
    synced_by: str | None = None,
) -> dict:
    """
    Sync selected PRJ_REL edges to UKL.

    Edge key format: "{from_key}--{rel_type}-->{to_key}"

    GUARDRAIL: Only syncs edges where both endpoints are already synced to UKL.

    Args:
        workspace_id: Tenant isolation
        project_id: Project scope
        edge_keys: List of PRJ_REL edge keys to sync
        synced_by: User identifier for audit log

    Returns:
        {
            "results": [{"edge_key": ..., "action": ...}, ...],
            "sync_log_id": ...
        }
    """
    ws = str(workspace_id)
    pid = str(project_id)
    results = []
    sync_log_id = uuid.uuid4()

    try:
        async with get_session() as session:
            for edge_key in edge_keys:
                # Parse edge key
                parts = edge_key.split("-->")
                if len(parts) != 2:
                    results.append({
                        "edge_key": edge_key,
                        "action": "invalid_format",
                    })
                    continue

                from_part = parts[0]
                to_key = parts[1]

                # Parse from_key and rel_type
                rel_parts = from_part.rsplit("--", 1)
                if len(rel_parts) != 2:
                    results.append({
                        "edge_key": edge_key,
                        "action": "invalid_format",
                    })
                    continue

                from_key = rel_parts[0]
                rel_type = rel_parts[1]

                # Check if both endpoints are synced to UKL
                result = await session.run(
                    """
                    MATCH (from_prj:PRJ_Node {workspace_id: $ws, project_id: $pid, key: $from_key})
                          -[:SYNCED_AS]->(from_ukl)
                    MATCH (to_prj:PRJ_Node {workspace_id: $ws, project_id: $pid, key: $to_key})
                          -[:SYNCED_AS]->(to_ukl)
                    RETURN from_ukl.key AS from_ukl_key,
                           to_ukl.key AS to_ukl_key,
                           labels(from_ukl) AS from_labels,
                           labels(to_ukl) AS to_labels
                    """,
                    ws=ws,
                    pid=pid,
                    from_key=from_key,
                    to_key=to_key,
                )
                record = await result.single()

                if not record:
                    results.append({
                        "edge_key": edge_key,
                        "action": "endpoints_not_synced",
                    })
                    continue

                # Create edge in UKL
                await session.run(
                    f"""
                    MATCH (from_prj:PRJ_Node {{workspace_id: $ws, project_id: $pid, key: $from_key}})
                          -[:SYNCED_AS]->(from_ukl)
                    MATCH (to_prj:PRJ_Node {{workspace_id: $ws, project_id: $pid, key: $to_key}})
                          -[:SYNCED_AS]->(to_ukl)
                    MERGE (from_ukl)-[r:{rel_type}]->(to_ukl)
                    SET r.synced_from_project = $pid,
                        r.sync_log_id = $sync_log_id,
                        r.synced_at = datetime()
                    """,
                    ws=ws,
                    pid=pid,
                    from_key=from_key,
                    to_key=to_key,
                    sync_log_id=str(sync_log_id),
                )

                results.append({
                    "edge_key": edge_key,
                    "action": "synced",
                })

        # Log sync in PostgreSQL
        Session = get_async_session()
        async with Session() as db_session:
            await db_session.execute(
                insert(ProjectSyncLog).values(
                    id=sync_log_id,
                    project_id=project_id,
                    workspace_id=workspace_id,
                    synced_node_keys=[],
                    synced_edge_keys=edge_keys,
                    ukl_entity_keys=[],
                    synced_by=synced_by,
                )
            )
            await db_session.commit()

        logger.info(
            "Synced %d PRJ edges to UKL (project=%s, sync_log=%s)",
            len(edge_keys), project_id, sync_log_id
        )

    except Exception as e:
        logger.error("Failed to sync PRJ edges to UKL: %s", e)
        raise

    return {
        "results": results,
        "sync_log_id": str(sync_log_id),
    }


async def get_sync_preview(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    node_keys: list[str],
    edge_keys: list[str] | None = None,
) -> dict:
    """
    Preview what would be synced without actually syncing.

    Returns details about each node/edge and what action would be taken.
    """
    ws = str(workspace_id)
    pid = str(project_id)
    node_previews = []
    edge_previews = []

    try:
        async with get_session() as session:
            # Preview nodes
            for prj_key in node_keys:
                result = await session.run(
                    """
                    MATCH (n:PRJ_Node {workspace_id: $ws, project_id: $pid, key: $key})
                    OPTIONAL MATCH (n)-[:SYNCED_AS]->(ukl)
                    RETURN n.node_type AS node_type,
                           n.name AS name,
                           n.properties AS properties,
                           n.status AS status,
                           ukl.key AS existing_ukl_key
                    """,
                    ws=ws,
                    pid=pid,
                    key=prj_key,
                )
                record = await result.single()

                if not record:
                    node_previews.append({
                        "prj_key": prj_key,
                        "action": "not_found",
                    })
                    continue

                if record["status"] == "synced":
                    node_previews.append({
                        "prj_key": prj_key,
                        "name": record["name"],
                        "node_type": record["node_type"],
                        "action": "already_synced",
                        "existing_ukl_key": record["existing_ukl_key"],
                    })
                    continue

                # Compute would-be UKL key
                props = _parse_properties(record["properties"])
                entity_dict = {
                    "type": record["node_type"],
                    "name": record["name"],
                    "email": props.get("email"),
                    "domain": props.get("domain"),
                }
                ukl_key = resolve_entity_key(entity_dict)
                ukl_label = LABEL_MAP.get(record["node_type"].lower(), "Topic")

                # Check if UKL entity exists
                existing = await session.run(
                    f"""
                    MATCH (e:{ukl_label} {{workspace_id: $ws, key: $ukl_key}})
                    RETURN e.name AS name
                    """,
                    ws=ws,
                    ukl_key=ukl_key,
                )
                existing_record = await existing.single()

                node_previews.append({
                    "prj_key": prj_key,
                    "name": record["name"],
                    "node_type": record["node_type"],
                    "target_ukl_key": ukl_key,
                    "target_ukl_label": ukl_label,
                    "action": "would_match" if existing_record else "would_create",
                    "existing_ukl_name": existing_record["name"] if existing_record else None,
                })

            # Preview edges
            for edge_key in (edge_keys or []):
                parts = edge_key.split("-->")
                if len(parts) != 2:
                    edge_previews.append({
                        "edge_key": edge_key,
                        "action": "invalid_format",
                    })
                    continue

                from_part = parts[0]
                to_key = parts[1]
                rel_parts = from_part.rsplit("--", 1)
                if len(rel_parts) != 2:
                    edge_previews.append({
                        "edge_key": edge_key,
                        "action": "invalid_format",
                    })
                    continue

                from_key = rel_parts[0]
                rel_type = rel_parts[1]

                # Check endpoints
                result = await session.run(
                    """
                    MATCH (from_prj:PRJ_Node {workspace_id: $ws, project_id: $pid, key: $from_key})
                    MATCH (to_prj:PRJ_Node {workspace_id: $ws, project_id: $pid, key: $to_key})
                    OPTIONAL MATCH (from_prj)-[:SYNCED_AS]->(from_ukl)
                    OPTIONAL MATCH (to_prj)-[:SYNCED_AS]->(to_ukl)
                    RETURN from_prj.name AS from_name,
                           to_prj.name AS to_name,
                           from_ukl.key AS from_ukl_key,
                           to_ukl.key AS to_ukl_key
                    """,
                    ws=ws,
                    pid=pid,
                    from_key=from_key,
                    to_key=to_key,
                )
                record = await result.single()

                if not record:
                    edge_previews.append({
                        "edge_key": edge_key,
                        "action": "endpoints_not_found",
                    })
                    continue

                if not record["from_ukl_key"] or not record["to_ukl_key"]:
                    edge_previews.append({
                        "edge_key": edge_key,
                        "from_name": record["from_name"],
                        "to_name": record["to_name"],
                        "rel_type": rel_type,
                        "action": "endpoints_not_synced",
                        "from_synced": record["from_ukl_key"] is not None,
                        "to_synced": record["to_ukl_key"] is not None,
                    })
                    continue

                edge_previews.append({
                    "edge_key": edge_key,
                    "from_name": record["from_name"],
                    "to_name": record["to_name"],
                    "rel_type": rel_type,
                    "action": "would_sync",
                    "from_ukl_key": record["from_ukl_key"],
                    "to_ukl_key": record["to_ukl_key"],
                })

    except Exception as e:
        logger.error("Failed to generate sync preview: %s", e)
        raise

    return {
        "nodes": node_previews,
        "edges": edge_previews,
    }


async def get_sync_log(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    limit: int = 50,
) -> list[dict]:
    """Get sync log entries for a project."""
    from sqlalchemy import select

    from app.models import ProjectSyncLog

    Session = get_async_session()

    async with Session() as session:
        result = await session.execute(
            select(ProjectSyncLog)
            .where(
                ProjectSyncLog.project_id == project_id,
                ProjectSyncLog.workspace_id == workspace_id,
            )
            .order_by(ProjectSyncLog.created_at.desc())
            .limit(limit)
        )
        logs = result.scalars().all()

    return [
        {
            "id": str(log.id),
            "project_id": str(log.project_id),
            "synced_node_keys": log.synced_node_keys,
            "synced_edge_keys": log.synced_edge_keys,
            "ukl_entity_keys": log.ukl_entity_keys,
            "synced_by": log.synced_by,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
