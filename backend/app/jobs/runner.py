"""
Postgres-based job runner.
Claims jobs via SELECT ... FOR UPDATE SKIP LOCKED for crash-safety.
"""

import asyncio
import logging
import traceback
from datetime import datetime, timedelta, timezone

from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models import Job, JobStatus

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
POLL_INTERVAL = 2  # seconds
BACKOFF_BASE = 30  # seconds

# Will be populated by register_handler()
_handlers: dict[str, object] = {}


def register_handler(job_type: str, fn):
    """Register an async handler for a job type."""
    _handlers[job_type] = fn


CLAIM_SQL = text("""
    UPDATE jobs
    SET status = 'running', attempts = attempts + 1, updated_at = now()
    WHERE id = (
        SELECT id FROM jobs
        WHERE status = 'queued'
          AND (run_after IS NULL OR run_after <= now())
          AND attempts < :max_attempts
        ORDER BY created_at
        FOR UPDATE SKIP LOCKED
        LIMIT 1
    )
    RETURNING id, workspace_id, type, payload_json, attempts
""")


async def claim_job(session: AsyncSession) -> dict | None:
    result = await session.execute(CLAIM_SQL, {"max_attempts": MAX_ATTEMPTS})
    row = result.mappings().first()
    if row:
        await session.commit()
        return dict(row)
    return None


async def mark_done(session: AsyncSession, job_id) -> None:
    await session.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(status=JobStatus.done, updated_at=datetime.now(timezone.utc))
    )
    await session.commit()


async def mark_failed(session: AsyncSession, job_id, error: str, attempts: int) -> None:
    run_after = datetime.now(timezone.utc) + timedelta(seconds=BACKOFF_BASE * attempts)
    await session.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(
            status=JobStatus.queued if attempts < MAX_ATTEMPTS else JobStatus.failed,
            last_error=error[:4000],
            run_after=run_after if attempts < MAX_ATTEMPTS else None,
            updated_at=datetime.now(timezone.utc),
        )
    )
    await session.commit()


async def process_job(job: dict) -> None:
    job_type = job["type"]
    handler = _handlers.get(job_type)
    if not handler:
        raise ValueError(f"No handler registered for job type: {job_type}")
    await handler(job["workspace_id"], job["payload_json"])


async def run_loop() -> None:
    logger.info("Job runner started – polling every %ss", POLL_INTERVAL)
    Session = get_async_session()

    while True:
        try:
            async with Session() as session:
                job = await claim_job(session)

            if job is None:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            logger.info("Claimed job %s type=%s attempt=%s", job["id"], job["type"], job["attempts"])

            try:
                t0 = asyncio.get_event_loop().time()
                await process_job(job)
                elapsed = asyncio.get_event_loop().time() - t0
                async with Session() as session:
                    await mark_done(session, job["id"])
                logger.info("Job %s type=%s done in %.2fs", job["id"], job["type"], elapsed)
            except Exception:
                tb = traceback.format_exc()
                logger.error("Job %s type=%s failed (attempt %s):\n%s", job["id"], job["type"], job["attempts"], tb)
                async with Session() as session:
                    await mark_failed(session, job["id"], tb, job["attempts"])

        except Exception:
            logger.exception("Runner loop error")
            await asyncio.sleep(POLL_INTERVAL)
