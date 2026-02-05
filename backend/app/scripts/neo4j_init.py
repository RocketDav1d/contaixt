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
