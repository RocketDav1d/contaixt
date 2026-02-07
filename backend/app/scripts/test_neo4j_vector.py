"""
Test script for Neo4j vector search.

Run via: python -m app.scripts.test_neo4j_vector

Tests:
1. Neo4j connectivity
2. Chunk nodes with embeddings exist
3. Vector similarity search works
4. Pre-filtering by workspace works
"""

import asyncio
import logging

from app.neo4j_client import get_session, verify_connectivity, close_driver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_connectivity() -> bool:
    """Test 1: Verify Neo4j is reachable."""
    logger.info("Test 1: Checking Neo4j connectivity...")
    result = await verify_connectivity()
    if result:
        logger.info("✓ Neo4j connectivity OK")
    else:
        logger.error("✗ Neo4j connectivity FAILED")
    return result


async def test_chunk_count() -> int:
    """Test 2: Count Chunk nodes with embeddings."""
    logger.info("Test 2: Counting Chunk nodes with embeddings...")
    async with get_session() as session:
        result = await session.run(
            "MATCH (c:Chunk) WHERE c.embedding IS NOT NULL RETURN count(c) AS count"
        )
        record = await result.single()
        count = record["count"] if record else 0

    if count > 0:
        logger.info("✓ Found %d Chunk nodes with embeddings", count)
    else:
        logger.warning("✗ No Chunk nodes with embeddings found")
    return count


async def test_vector_index() -> bool:
    """Test 3: Verify vector index exists."""
    logger.info("Test 3: Checking vector index...")
    async with get_session() as session:
        result = await session.run(
            "SHOW INDEXES YIELD name, type WHERE type = 'VECTOR' RETURN name"
        )
        records = await result.data()

    if records:
        logger.info("✓ Vector indexes found: %s", [r["name"] for r in records])
        return True
    else:
        logger.warning("✗ No vector index found")
        return False


async def test_similarity_search() -> bool:
    """Test 4: Test vector similarity search with a real embedding."""
    logger.info("Test 4: Testing vector similarity search...")

    async with get_session() as session:
        # Get a random chunk's embedding to use as query
        result = await session.run(
            """
            MATCH (c:Chunk)
            WHERE c.embedding IS NOT NULL
            RETURN c.chunk_id AS chunk_id,
                   c.workspace_id AS workspace_id,
                   c.embedding AS embedding,
                   c.text AS text
            LIMIT 1
            """
        )
        record = await result.single()

    if not record:
        logger.warning("✗ No chunks to test with")
        return False

    test_embedding = record["embedding"]
    workspace_id = record["workspace_id"]
    source_chunk_id = record["chunk_id"]

    logger.info("  Using chunk %s as query vector", source_chunk_id)
    logger.info("  Workspace: %s", workspace_id)

    # Now search for similar chunks
    async with get_session() as session:
        result = await session.run(
            """
            MATCH (chunk:Chunk)
            WHERE chunk.workspace_id = $ws
              AND chunk.embedding IS NOT NULL
            WITH chunk, vector.similarity.cosine(chunk.embedding, $embedding) AS score
            WHERE score > 0.0
            ORDER BY score DESC
            LIMIT 5
            RETURN chunk.chunk_id AS chunk_id,
                   score,
                   substring(chunk.text, 0, 80) AS text_preview
            """,
            ws=workspace_id,
            embedding=list(test_embedding),
        )
        records = await result.data()

    if records:
        logger.info("✓ Vector search returned %d results:", len(records))
        for r in records:
            logger.info("    - %s (score: %.4f): %s...", r["chunk_id"], r["score"], r["text_preview"])
        return True
    else:
        logger.warning("✗ Vector search returned no results")
        return False


async def test_prefiltering() -> bool:
    """Test 5: Verify pre-filtering isolates workspaces."""
    logger.info("Test 5: Testing workspace pre-filtering...")

    async with get_session() as session:
        # Get distinct workspace IDs
        result = await session.run(
            "MATCH (c:Chunk) RETURN DISTINCT c.workspace_id AS ws LIMIT 5"
        )
        records = await result.data()

    workspaces = [r["ws"] for r in records if r["ws"]]
    logger.info("  Found %d distinct workspaces", len(workspaces))

    if len(workspaces) < 1:
        logger.warning("✗ No workspaces found")
        return False

    # Search with a fake workspace ID - should return nothing
    fake_ws = "00000000-0000-0000-0000-000000000000"

    async with get_session() as session:
        # Get any embedding to use
        result = await session.run(
            "MATCH (c:Chunk) WHERE c.embedding IS NOT NULL RETURN c.embedding AS embedding LIMIT 1"
        )
        record = await result.single()

    if not record:
        logger.warning("✗ No embeddings to test with")
        return False

    test_embedding = record["embedding"]

    async with get_session() as session:
        result = await session.run(
            """
            MATCH (chunk:Chunk)
            WHERE chunk.workspace_id = $ws
              AND chunk.embedding IS NOT NULL
            WITH chunk, vector.similarity.cosine(chunk.embedding, $embedding) AS score
            WHERE score > 0.0
            RETURN count(chunk) AS count
            """,
            ws=fake_ws,
            embedding=list(test_embedding),
        )
        record = await result.single()
        count = record["count"] if record else 0

    if count == 0:
        logger.info("✓ Pre-filtering works: fake workspace returned 0 results")
        return True
    else:
        logger.error("✗ Pre-filtering FAILED: fake workspace returned %d results", count)
        return False


async def main() -> None:
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Neo4j Vector Search Test Suite")
    logger.info("=" * 60)

    results = {}

    try:
        results["connectivity"] = await test_connectivity()
        if not results["connectivity"]:
            logger.error("Cannot continue without connectivity")
            return

        results["chunk_count"] = await test_chunk_count() > 0
        results["vector_index"] = await test_vector_index()
        results["similarity_search"] = await test_similarity_search()
        results["prefiltering"] = await test_prefiltering()

    finally:
        await close_driver()

    # Summary
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info("  %s: %s", name, status)
    logger.info("-" * 60)
    logger.info("  %d/%d tests passed", passed, total)

    if passed == total:
        logger.info("All tests passed! Neo4j vector search is working.")
    else:
        logger.warning("Some tests failed. Check the output above.")


if __name__ == "__main__":
    asyncio.run(main())
