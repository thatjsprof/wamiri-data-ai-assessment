from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.models import Job
from ..common.time import utcnow

class JobRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, job_id: str, document_id: str) -> Job:
        now = utcnow()
        job = Job(
            id=job_id,
            document_id=document_id,
            status="queued",
            created_at=now,
            updated_at=now,
            started_at=None,
            completed_at=None,
            outputs={},
            error=None,
            review_item_id=None,
        )
        self.session.add(job)
        return job

    async def get(self, job_id: str) -> Job | None:
        return await self.session.get(Job, job_id)

    async def mark_started(self, job_id: str) -> None:
        job = await self.session.get(Job, job_id)
        if not job:
            raise KeyError("job_not_found")
        job.status = "processing"
        job.started_at = utcnow()
        job.updated_at = utcnow()

    async def mark_completed(self, job_id: str, status: str) -> None:
        job = await self.session.get(Job, job_id)
        if not job:
            raise KeyError("job_not_found")
        job.status = status
        job.completed_at = utcnow()
        job.updated_at = utcnow()

    async def set_status(self, job_id: str, status: str, error: str | None = None) -> None:
        job = await self.session.get(Job, job_id)
        if not job:
            raise KeyError("job_not_found")
        job.status = status
        job.error = error
        job.updated_at = utcnow()

    async def set_outputs(self, job_id: str, outputs: dict) -> None:
        job = await self.session.get(Job, job_id)
        if not job:
            raise KeyError("job_not_found")
        job.outputs = outputs
        job.updated_at = utcnow()

    async def set_review_item(self, job_id: str, review_item_id: str) -> None:
        job = await self.session.get(Job, job_id)
        if not job:
            raise KeyError("job_not_found")
        job.review_item_id = review_item_id
        job.updated_at = utcnow()
