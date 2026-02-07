"""Project Graph operations for PRJ_Node and PRJ_REL.

Phase 16: Project Graph Layer - Isolated graph for reasoning and exploration.

GUARDRAIL: This module ONLY writes to :PRJ_Node and :PRJ_REL labels.
UKL entities (Person, Company, Topic, Document, Chunk) are never touched here.
"""

import json
import logging
import uuid

from app.neo4j_client import get_session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PRJ_Node Operations
# ---------------------------------------------------------------------------


async def write_prj_node(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    key: str,
    node_type: str,
    name: str,
    properties: dict | None = None,
    ukl_ref: str | None = None,
    source_message_id: uuid.UUID | None = None,
) -> str:
    """
    Create or update a PRJ_Node.

    GUARDRAIL: Only writes to :PRJ_Node label.

    Args:
        workspace_id: Tenant isolation
        project_id: Project scope
        key: Unique key within project (e.g., "prj:person:john-doe")
        node_type: Type of node (person, company, topic, claim, etc.)
        name: Display name
        properties: Flexible key-value properties
        ukl_ref: Optional read-only reference to UKL entity key
        source_message_id: Chat message that created this node

    Returns:
        The node key
    """
    ws = str(workspace_id)
    pid = str(project_id)
    # Serialize properties as JSON string for Neo4j storage
    props_json = json.dumps(properties) if properties else "{}"
    msg_id = str(source_message_id) if source_message_id else None

    # Generate key if "auto"
    if key == "auto":
        key = f"prj:{node_type}:{uuid.uuid4().hex[:8]}"

    try:
        async with get_session() as session:
            await session.run(
                """
                MERGE (n:PRJ_Node {workspace_id: $ws, project_id: $pid, key: $key})
                ON CREATE SET n.created_at = datetime(), n.status = 'draft'
                SET n.node_type = $node_type,
                    n.name = $name,
                    n.properties = $props_json,
                    n.ukl_ref = $ukl_ref,
                    n.source_message_id = $msg_id,
                    n.updated_at = datetime()
                """,
                ws=ws,
                pid=pid,
                key=key,
                node_type=node_type,
                name=name,
                props_json=props_json,
                ukl_ref=ukl_ref,
                msg_id=msg_id,
            )

        logger.info("Wrote PRJ_Node: %s (project=%s)", key, project_id)
        return key

    except Exception as e:
        logger.error("Failed to write PRJ_Node: %s", e)
        raise


async def write_prj_edge(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    from_key: str,
    to_key: str,
    rel_type: str,
    properties: dict | None = None,
    source_message_id: uuid.UUID | None = None,
) -> str:
    """
    Create or update a PRJ_REL edge between two PRJ_Nodes.

    GUARDRAIL: Only writes relationships between :PRJ_Node labels.

    Args:
        workspace_id: Tenant isolation
        project_id: Project scope
        from_key: Source node key
        to_key: Target node key
        rel_type: Relationship type (e.g., WORKS_AT, KNOWS)
        properties: Flexible key-value properties
        source_message_id: Chat message that created this edge

    Returns:
        Edge key in format "{from_key}--{rel_type}-->{to_key}"
    """
    ws = str(workspace_id)
    pid = str(project_id)
    # Serialize properties as JSON string for Neo4j storage
    props_json = json.dumps(properties) if properties else "{}"
    msg_id = str(source_message_id) if source_message_id else None
    edge_key = f"{from_key}--{rel_type}-->{to_key}"

    try:
        async with get_session() as session:
            await session.run(
                """
                MATCH (a:PRJ_Node {workspace_id: $ws, project_id: $pid, key: $from_key})
                MATCH (b:PRJ_Node {workspace_id: $ws, project_id: $pid, key: $to_key})
                MERGE (a)-[r:PRJ_REL {workspace_id: $ws, project_id: $pid, rel_type: $rel_type}]->(b)
                ON CREATE SET r.created_at = datetime()
                SET r.properties = $props_json,
                    r.source_message_id = $msg_id,
                    r.updated_at = datetime()
                """,
                ws=ws,
                pid=pid,
                from_key=from_key,
                to_key=to_key,
                rel_type=rel_type,
                props_json=props_json,
                msg_id=msg_id,
            )

        logger.info("Wrote PRJ_REL: %s (project=%s)", edge_key, project_id)
        return edge_key

    except Exception as e:
        logger.error("Failed to write PRJ_REL: %s", e)
        raise


async def create_ukl_reference(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    prj_key: str,
    ukl_key: str,
    ref_type: str = "references",
) -> None:
    """
    Create a REFS_UKL edge from PRJ_Node to UKL entity (read-only reference).

    This allows PRJ nodes to reference UKL entities without modifying them.

    Args:
        workspace_id: Tenant isolation
        project_id: Project scope
        prj_key: PRJ_Node key
        ukl_key: UKL entity key (e.g., "person:email:john@acme.com")
        ref_type: Type of reference (e.g., "analyzes", "compares_to", "extends")
    """
    ws = str(workspace_id)
    pid = str(project_id)

    try:
        async with get_session() as session:
            # Find the UKL entity by key (could be Person, Company, or Topic)
            await session.run(
                """
                MATCH (prj:PRJ_Node {workspace_id: $ws, project_id: $pid, key: $prj_key})
                MATCH (ukl {workspace_id: $ws, key: $ukl_key})
                MERGE (prj)-[r:REFS_UKL]->(ukl)
                SET r.ref_type = $ref_type,
                    r.created_at = datetime()
                """,
                ws=ws,
                pid=pid,
                prj_key=prj_key,
                ukl_key=ukl_key,
                ref_type=ref_type,
            )

        logger.info("Created REFS_UKL: %s -> %s", prj_key, ukl_key)

    except Exception as e:
        logger.error("Failed to create REFS_UKL: %s", e)
        raise


# ---------------------------------------------------------------------------
# Read Operations
# ---------------------------------------------------------------------------


async def get_project_graph(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
) -> dict:
    """
    Get all nodes and edges for a project graph (for UI visualization).

    Returns:
        {
            "nodes": [{"key": ..., "node_type": ..., "name": ..., ...}],
            "edges": [{"from_key": ..., "to_key": ..., "rel_type": ..., ...}]
        }
    """
    ws = str(workspace_id)
    pid = str(project_id)

    nodes = []
    edges = []

    try:
        async with get_session() as session:
            # Get all PRJ_Nodes
            result = await session.run(
                """
                MATCH (n:PRJ_Node {workspace_id: $ws, project_id: $pid})
                OPTIONAL MATCH (n)-[:SYNCED_AS]->()
                WITH n, count(*) > 0 AS synced_to_ukl
                RETURN n.key AS key,
                       n.node_type AS node_type,
                       n.name AS name,
                       n.properties AS properties,
                       n.ukl_ref AS ukl_ref,
                       n.status AS status,
                       n.source_message_id AS source_message_id,
                       synced_to_ukl,
                       n.created_at AS created_at,
                       n.updated_at AS updated_at
                """,
                ws=ws,
                pid=pid,
            )
            records = await result.data()

            for r in records:
                # Parse properties from JSON string
                props = r["properties"]
                if isinstance(props, str):
                    props = json.loads(props) if props else {}
                else:
                    props = props or {}
                nodes.append({
                    "key": r["key"],
                    "node_type": r["node_type"],
                    "name": r["name"],
                    "properties": props,
                    "ukl_ref": r["ukl_ref"],
                    "status": r["status"],
                    "source_message_id": r["source_message_id"],
                    "synced_to_ukl": r["synced_to_ukl"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
                })

            # Get all PRJ_REL edges
            result = await session.run(
                """
                MATCH (a:PRJ_Node {workspace_id: $ws, project_id: $pid})
                      -[r:PRJ_REL {workspace_id: $ws, project_id: $pid}]->
                      (b:PRJ_Node {workspace_id: $ws, project_id: $pid})
                RETURN a.key AS from_key,
                       b.key AS to_key,
                       r.rel_type AS rel_type,
                       r.properties AS properties,
                       r.source_message_id AS source_message_id,
                       r.created_at AS created_at
                """,
                ws=ws,
                pid=pid,
            )
            records = await result.data()

            for r in records:
                # Parse properties from JSON string
                props = r["properties"]
                if isinstance(props, str):
                    props = json.loads(props) if props else {}
                else:
                    props = props or {}
                edges.append({
                    "from_key": r["from_key"],
                    "to_key": r["to_key"],
                    "rel_type": r["rel_type"],
                    "properties": props,
                    "source_message_id": r["source_message_id"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                })

        logger.info(
            "Retrieved project graph: %d nodes, %d edges (project=%s)",
            len(nodes), len(edges), project_id
        )

    except Exception as e:
        logger.error("Failed to get project graph: %s", e)
        raise

    return {"nodes": nodes, "edges": edges}


async def get_prj_node(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    key: str,
) -> dict | None:
    """Get a single PRJ_Node by key."""
    ws = str(workspace_id)
    pid = str(project_id)

    try:
        async with get_session() as session:
            result = await session.run(
                """
                MATCH (n:PRJ_Node {workspace_id: $ws, project_id: $pid, key: $key})
                RETURN n.key AS key,
                       n.node_type AS node_type,
                       n.name AS name,
                       n.properties AS properties,
                       n.ukl_ref AS ukl_ref,
                       n.status AS status,
                       n.source_message_id AS source_message_id
                """,
                ws=ws,
                pid=pid,
                key=key,
            )
            record = await result.single()

            if not record:
                return None

            # Parse properties from JSON string
            props = record["properties"]
            if isinstance(props, str):
                props = json.loads(props) if props else {}
            else:
                props = props or {}

            return {
                "key": record["key"],
                "node_type": record["node_type"],
                "name": record["name"],
                "properties": props,
                "ukl_ref": record["ukl_ref"],
                "status": record["status"],
                "source_message_id": record["source_message_id"],
            }

    except Exception as e:
        logger.error("Failed to get PRJ_Node: %s", e)
        raise


# ---------------------------------------------------------------------------
# Delete Operations
# ---------------------------------------------------------------------------


async def delete_prj_node(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    key: str,
) -> bool:
    """Delete a PRJ_Node and its edges."""
    ws = str(workspace_id)
    pid = str(project_id)

    try:
        async with get_session() as session:
            # Delete edges first
            await session.run(
                """
                MATCH (n:PRJ_Node {workspace_id: $ws, project_id: $pid, key: $key})
                      -[r]-()
                DELETE r
                """,
                ws=ws,
                pid=pid,
                key=key,
            )

            # Delete node
            result = await session.run(
                """
                MATCH (n:PRJ_Node {workspace_id: $ws, project_id: $pid, key: $key})
                DELETE n
                RETURN count(n) AS deleted
                """,
                ws=ws,
                pid=pid,
                key=key,
            )
            record = await result.single()
            deleted = record["deleted"] if record else 0

        logger.info("Deleted PRJ_Node: %s (deleted=%d)", key, deleted)
        return deleted > 0

    except Exception as e:
        logger.error("Failed to delete PRJ_Node: %s", e)
        raise


async def delete_project_graph(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
) -> int:
    """Delete all PRJ_Nodes and PRJ_RELs for a project."""
    ws = str(workspace_id)
    pid = str(project_id)

    try:
        async with get_session() as session:
            # Delete all edges for this project
            await session.run(
                """
                MATCH (n:PRJ_Node {workspace_id: $ws, project_id: $pid})
                      -[r]-()
                DELETE r
                """,
                ws=ws,
                pid=pid,
            )

            # Delete all nodes for this project
            result = await session.run(
                """
                MATCH (n:PRJ_Node {workspace_id: $ws, project_id: $pid})
                DELETE n
                RETURN count(n) AS deleted
                """,
                ws=ws,
                pid=pid,
            )
            record = await result.single()
            deleted = record["deleted"] if record else 0

        logger.info("Deleted project graph: %d nodes (project=%s)", deleted, project_id)
        return deleted

    except Exception as e:
        logger.error("Failed to delete project graph: %s", e)
        raise
