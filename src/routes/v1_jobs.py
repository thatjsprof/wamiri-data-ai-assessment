from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.engine import get_session
from ..repositories.jobs import JobRepo
from ..repositories.documents import DocumentRepo
from ..schemas.responses import JobStatusResponse

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str, session: AsyncSession = Depends(get_session)):
    jobs = JobRepo(session)
    docs = DocumentRepo(session)

    job = await jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job_not_found")

    doc = await docs.get(job.document_id)

    return JobStatusResponse(
        job_id=job.id,
        document_id=job.document_id,
        status=job.status,
        error=job.error,
        outputs=job.outputs or {},
        review_item_id=job.review_item_id,
        extraction=(doc.extraction_json if doc else None),
    )
