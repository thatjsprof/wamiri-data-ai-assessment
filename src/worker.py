from __future__ import annotations

import asyncio
import base64
from celery import Celery

from .settings import settings
from .db.engine import SessionLocal, engine
from .db.base import Base
from .repositories.documents import DocumentRepo
from .repositories.jobs import JobRepo
from .repositories.audit import AuditRepo
from .repositories.review_queue import ReviewQueueRepo
from .workflow.context import WorkflowContext
from .workflow.runner import WorkflowRunner
from .observability.metrics import DOCS_PROCESSED, DOC_PROCESS_LATENCY, ERRORS
from .monitoring import maybe_start_sla_scheduler


celery_app = Celery("docproc", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1


async def _ensure_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@celery_app.on_after_configure.connect
def _setup_periodic_tasks(sender, **kwargs):
    # Optional: run SLA evaluation every minute (works when running celery beat).
    maybe_start_sla_scheduler(sender)


@celery_app.task(
    name="src.worker.process_document",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def process_document(
    job_id: str, document_id: str, content_type: str, file_b64: str
) -> dict:
    return asyncio.run(_process_async(job_id, document_id, content_type, file_b64))


async def _process_async(
    job_id: str, document_id: str, content_type: str, file_b64: str
) -> dict:
    await _ensure_tables()
    file_bytes = base64.b64decode(file_b64)

    async with SessionLocal() as session:
        docs = DocumentRepo(session)
        jobs = JobRepo(session)
        audit = AuditRepo(session)
        review = ReviewQueueRepo(session)

        await jobs.mark_started(job_id)
        await docs.set_status(document_id, "processing")
        await audit.append(
            document_id,
            "system",
            "processing_started",
            {"content_type": content_type},
            job_id=job_id,
        )
        await session.commit()

        try:
            doc = await docs.get(document_id)
            locked = (doc.locked_fields if doc else {}) or {}

            ctx = WorkflowContext(
                job_id=job_id,
                document_id=document_id,
                content_type=content_type,
                file_bytes=file_bytes,
                locked_fields=locked,
            )

            runner = WorkflowRunner()

            with DOC_PROCESS_LATENCY.time():
                await runner.run(
                    ctx,
                    injected_cfg={
                        "session": session,
                        "docs": docs,
                        "jobs": jobs,
                        "audit": audit,
                        "review": review,
                    },
                )

            status = "review_pending" if ctx.needs_review else "completed"
            await jobs.mark_completed(job_id, status)
            DOCS_PROCESSED.labels(status=status).inc()

            await session.commit()

            job = await jobs.get(job_id)
            return {
                "job_id": job_id,
                "document_id": document_id,
                "status": status,
                "review_item_id": job.review_item_id if job else None,
                "outputs": job.outputs if job else {},
            }

        except Exception as e:
            ERRORS.inc()
            await jobs.set_status(job_id, "failed", error=type(e).__name__)
            await docs.set_status(document_id, "failed")
            await audit.append(
                document_id,
                "system",
                "processing_failed",
                {"error": type(e).__name__},
                job_id=job_id,
            )
            await session.commit()
            raise
