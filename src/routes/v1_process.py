from __future__ import annotations

import base64
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException

from src.db.engine import SessionLocal
from src.repositories.documents import DocumentRepo
from src.repositories.jobs import JobRepo
from src.repositories.audit import AuditRepo
from src.settings import settings
from celery import Celery

router = APIRouter(tags=["process"])
celery_client = Celery(
    "docproc_client", broker=settings.redis_url, backend=settings.redis_url
)


@router.post("/process")
async def process(file: UploadFile = File(...)) -> dict:
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    content_type = file.content_type or "application/octet-stream"
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    document_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    async with SessionLocal() as session:
        docs = DocumentRepo(session)
        jobs = JobRepo(session)
        audit = AuditRepo(session)

        async with session.begin():
            await docs.create(
                document_id=document_id,
                status="queued",
            )

            await jobs.create(
                job_id=job_id,
                document_id=document_id,
            )

            await session.flush()

            await audit.append(
                document_id,
                "system",
                "received",
                {"filename": file.filename, "content_type": content_type},
                job_id=job_id,
            )

    celery_client.send_task(
        "src.worker.process_document",
        args=[
            job_id,
            document_id,
            content_type,
            base64.b64encode(file_bytes).decode("utf-8"),
        ],
    )

    return {"job_id": job_id, "document_id": document_id}
