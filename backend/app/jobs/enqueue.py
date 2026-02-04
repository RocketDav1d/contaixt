"""Helper to enqueue jobs into the Postgres job table."""

import uuid

from sqlalchemy import insert

from app.db import get_async_session
from app.models import Job, JobType


async def enqueue_job(workspace_id: uuid.UUID, job_type: JobType, payload: dict) -> uuid.UUID:
    Session = get_async_session()
    job_id = uuid.uuid4()
    async with Session() as session:
        await session.execute(
            insert(Job).values(
                id=job_id,
                workspace_id=workspace_id,
                type=job_type,
                payload_json=payload,
            )
        )
        await session.commit()
    return job_id
