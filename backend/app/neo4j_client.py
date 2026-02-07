"""
Neo4j async driver singleton.

Per Neo4j best practices, drivers should be application-scoped singletons:
- Drivers manage connection pools and are expensive to create
- Creating/closing drivers per request adds latency and bypasses pooling
- Sessions are cheap and should be created per-operation

Reference: https://neo4j.com/blog/developer/neo4j-driver-best-practices/
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

# Application-scoped singleton driver
_driver: AsyncDriver | None = None


def get_driver() -> AsyncDriver:
    """
    Get the singleton Neo4j async driver.

    Creates the driver on first call and reuses it for all subsequent calls.
    The driver manages its own connection pool internally.
    """
    global _driver

    if _driver is None:
        logger.info("Creating Neo4j async driver for %s", settings.neo4j_uri)
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
            # Connection pool settings
            max_connection_pool_size=50,  # Adjust based on expected concurrency
            connection_acquisition_timeout=60.0,  # Wait up to 60s for a connection
        )

    return _driver


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a Neo4j session from the singleton driver.

    Sessions are cheap - create one per operation/transaction.
    This context manager ensures proper cleanup.

    Usage:
        async with get_session() as session:
            result = await session.run("MATCH (n) RETURN n LIMIT 10")
            records = await result.data()
    """
    driver = get_driver()
    session = driver.session(database=settings.neo4j_database)
    try:
        yield session
    finally:
        await session.close()


async def verify_connectivity() -> bool:
    """
    Verify Neo4j connectivity at startup.

    Should be called during application startup to fail fast if
    Neo4j is unreachable or credentials are wrong.
    """
    try:
        driver = get_driver()
        await driver.verify_connectivity()
        logger.info("Neo4j connectivity verified")
        return True
    except Exception as e:
        logger.error("Neo4j connectivity check failed: %s", e)
        return False


async def close_driver() -> None:
    """
    Close the Neo4j driver.

    Should be called during application shutdown to cleanly close
    all connections in the pool.
    """
    global _driver

    if _driver is not None:
        logger.info("Closing Neo4j driver")
        await _driver.close()
        _driver = None
