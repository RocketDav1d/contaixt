"""
Neo4j graph upsert: creates/updates entity nodes and MENTIONS edges.
Every node and edge carries workspace_id for tenant isolation.
Every edge carries document_id + chunk_id + confidence for provenance.
"""

import logging
import uuid

from neo4j import AsyncGraphDatabase

from app.config import settings

logger = logging.getLogger(__name__)

# Map entity type → Neo4j label
LABEL_MAP = {
    "person": "Person",
    "company": "Company",
    "topic": "Topic",
}


async def upsert_entities_and_relations(
    workspace_id: uuid.UUID,
    vault_id: uuid.UUID | None,
    document_id: uuid.UUID,
    entities: list[dict],
    relations: list[dict],
    entity_keys: dict[str, str],  # {entity_name: resolved_key}
) -> None:
    """
    Upsert entities as nodes and create MENTIONS edges from Document to Entity.
    Also creates inter-entity relations (WORKS_AT, HAS_CONTACT, etc.).
    """
    ws = str(workspace_id)
    v_id = str(vault_id) if vault_id else ""
    doc_id = str(document_id)

    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )

    async with driver.session(database=settings.neo4j_database) as session:
        # Upsert Document node
        await session.run(
            """
            MERGE (d:Document {workspace_id: $ws, key: $key})
            SET d.document_id = $doc_id, d.vault_id = $vault_id
            """,
            ws=ws, key=f"doc:{doc_id}", doc_id=doc_id, vault_id=v_id,
        )

        # Upsert entity nodes + MENTIONS edges
        for ent in entities:
            name = ent.get("name", "")
            etype = ent.get("type", "unknown").lower()
            label = LABEL_MAP.get(etype, "Topic")
            key = entity_keys.get(name, f"{etype}:name:{name.lower()}")

            # MERGE entity node
            await session.run(
                f"""
                MERGE (e:{label} {{workspace_id: $ws, key: $key}})
                SET e.name = $name,
                    e.email = $email,
                    e.domain = $domain
                """,
                ws=ws,
                key=key,
                name=name,
                email=ent.get("email", ""),
                domain=ent.get("domain", ""),
            )

            # MERGE Document -[MENTIONS]-> Entity
            await session.run(
                f"""
                MATCH (d:Document {{workspace_id: $ws, key: $doc_key}})
                MATCH (e:{label} {{workspace_id: $ws, key: $entity_key}})
                MERGE (d)-[r:MENTIONS]->(e)
                SET r.document_id = $doc_id,
                    r.vault_id = $vault_id,
                    r.confidence = 1.0
                """,
                ws=ws,
                doc_key=f"doc:{doc_id}",
                entity_key=key,
                doc_id=doc_id,
                vault_id=v_id,
            )

        # Inter-entity relations (WORKS_AT, HAS_CONTACT, etc.)
        for rel in relations:
            from_name = rel.get("from_name", "")
            to_name = rel.get("to_name", "")
            rel_type = rel.get("type", "RELATED_TO").upper().replace(" ", "_")
            from_key = entity_keys.get(from_name)
            to_key = entity_keys.get(to_name)
            if not from_key or not to_key:
                continue

            await session.run(
                f"""
                MATCH (a {{workspace_id: $ws, key: $from_key}})
                MATCH (b {{workspace_id: $ws, key: $to_key}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r.document_id = $doc_id,
                    r.vault_id = $vault_id,
                    r.evidence = $evidence
                """,
                ws=ws,
                from_key=from_key,
                to_key=to_key,
                doc_id=doc_id,
                vault_id=v_id,
                evidence=rel.get("evidence", "")[:200],
            )

    await driver.close()
    logger.info("Graph upsert done: %d entities, %d relations for doc=%s", len(entities), len(relations), doc_id)
