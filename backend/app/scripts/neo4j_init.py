"""
Idempotent Neo4j schema init: constraints + indexes.
Run via: python -m app.scripts.neo4j_init
"""

import logging

from neo4j import GraphDatabase

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Each statement is idempotent (IF NOT EXISTS)
STATEMENTS = [
    # --- Uniqueness constraints (workspace_id + key per label) ---
    """
    CREATE CONSTRAINT person_workspace_key IF NOT EXISTS
    FOR (n:Person) REQUIRE (n.workspace_id, n.key) IS UNIQUE
    """,
    """
    CREATE CONSTRAINT company_workspace_key IF NOT EXISTS
    FOR (n:Company) REQUIRE (n.workspace_id, n.key) IS UNIQUE
    """,
    """
    CREATE CONSTRAINT topic_workspace_key IF NOT EXISTS
    FOR (n:Topic) REQUIRE (n.workspace_id, n.key) IS UNIQUE
    """,
    """
    CREATE CONSTRAINT document_workspace_key IF NOT EXISTS
    FOR (n:Document) REQUIRE (n.workspace_id, n.key) IS UNIQUE
    """,
    # --- Indexes for faster lookups ---
    """
    CREATE INDEX person_workspace_idx IF NOT EXISTS
    FOR (n:Person) ON (n.workspace_id)
    """,
    """
    CREATE INDEX company_workspace_idx IF NOT EXISTS
    FOR (n:Company) ON (n.workspace_id)
    """,
    """
    CREATE INDEX topic_workspace_idx IF NOT EXISTS
    FOR (n:Topic) ON (n.workspace_id)
    """,
    """
    CREATE INDEX document_workspace_idx IF NOT EXISTS
    FOR (n:Document) ON (n.workspace_id)
    """,
    # --- Vault index on Document nodes ---
    """
    CREATE INDEX document_vault_idx IF NOT EXISTS
    FOR (n:Document) ON (n.vault_id)
    """,
    # --- Chunk nodes for vector search ---
    """
    CREATE CONSTRAINT chunk_workspace_doc_idx IF NOT EXISTS
    FOR (n:Chunk) REQUIRE (n.workspace_id, n.document_id, n.idx) IS UNIQUE
    """,
    """
    CREATE INDEX chunk_workspace_idx IF NOT EXISTS
    FOR (n:Chunk) ON (n.workspace_id)
    """,
    """
    CREATE INDEX chunk_document_idx IF NOT EXISTS
    FOR (n:Chunk) ON (n.document_id)
    """,
    """
    CREATE INDEX chunk_connection_idx IF NOT EXISTS
    FOR (n:Chunk) ON (n.source_connection_id)
    """,
    # --- Vector index for semantic search (HNSW, cosine similarity) ---
    # Note: WITH [n.prop] filtering properties syntax requires Neo4j 2026.01+
    # Neo4j Aura 5.x uses basic syntax. Pre-filtering still works via Cypher WHERE.
    # Reference: https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/
    """
    CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
    FOR (n:Chunk) ON (n.embedding)
    OPTIONS {indexConfig: {
        `vector.dimensions`: 1536,
        `vector.similarity_function`: 'cosine'
    }}
    """,
    # --- PRJ_Node: Project Graph nodes (isolated from UKL) ---
    # Phase 16: Project Graph Layer
    """
    CREATE CONSTRAINT prj_node_workspace_project_key IF NOT EXISTS
    FOR (n:PRJ_Node) REQUIRE (n.workspace_id, n.project_id, n.key) IS UNIQUE
    """,
    """
    CREATE INDEX prj_node_project_idx IF NOT EXISTS
    FOR (n:PRJ_Node) ON (n.project_id)
    """,
    """
    CREATE INDEX prj_node_workspace_idx IF NOT EXISTS
    FOR (n:PRJ_Node) ON (n.workspace_id)
    """,
    """
    CREATE INDEX prj_node_type_idx IF NOT EXISTS
    FOR (n:PRJ_Node) ON (n.node_type)
    """,
    """
    CREATE INDEX prj_node_status_idx IF NOT EXISTS
    FOR (n:PRJ_Node) ON (n.status)
    """,
]


def run() -> None:
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )
    with driver.session(database=settings.neo4j_database) as session:
        for stmt in STATEMENTS:
            logger.info("Running: %s", stmt.strip().split("\n")[1].strip())
            session.run(stmt)
    driver.close()
    logger.info("Neo4j schema init done.")


if __name__ == "__main__":
    run()
