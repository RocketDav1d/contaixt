"""
Job observability endpoints.
"""

import uuid

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.db import get_async_session
from app.models import Job, JobStatus, JobType

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


class JobStats(BaseModel):
    type: str
    status: str
    count: int


class JobStatsResponse(BaseModel):
    stats: list[JobStats]
    total: int
    queued: int
    running: int
    done: int
    failed: int


@router.get("/stats", response_model=JobStatsResponse)
async def job_stats(workspace_id: uuid.UUID = Query(...)):
    Session = get_async_session()
    async with Session() as session:
        # Grouped stats
        result = await session.execute(
            select(Job.type, Job.status, func.count())
            .where(Job.workspace_id == workspace_id)
            .group_by(Job.type, Job.status)
            .order_by(Job.type, Job.status)
        )
        rows = result.fetchall()

        # Totals by status
        totals = await session.execute(
            select(Job.status, func.count())
            .where(Job.workspace_id == workspace_id)
            .group_by(Job.status)
        )
        total_map = {str(r[0].value): r[1] for r in totals.fetchall()}

    stats = [JobStats(type=r[0].value, status=r[1].value, count=r[2]) for r in rows]
    total = sum(s.count for s in stats)

    return JobStatsResponse(
        stats=stats,
        total=total,
        queued=total_map.get("queued", 0),
        running=total_map.get("running", 0),
        done=total_map.get("done", 0),
        failed=total_map.get("failed", 0),
    )


class FailedJob(BaseModel):
    id: uuid.UUID
    type: str
    last_error: str | None
    attempts: int


@router.get("/failed", response_model=list[FailedJob])
async def failed_jobs(workspace_id: uuid.UUID = Query(...), limit: int = Query(20, le=100)):
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(Job.id, Job.type, Job.last_error, Job.attempts)
            .where(
                Job.workspace_id == workspace_id,
                Job.status == JobStatus.failed,
            )
            .order_by(Job.updated_at.desc())
            .limit(limit)
        )
        rows = result.fetchall()

    return [FailedJob(id=r.id, type=r.type.value, last_error=r.last_error, attempts=r.attempts) for r in rows]
