from __future__ import annotations

from .registry import register
from ..context import WorkflowContext
from ...repositories.documents import DocumentRepo
from ...repositories.jobs import JobRepo
from ...repositories.audit import AuditRepo


@register("persist")
async def run(ctx: WorkflowContext, cfg: dict) -> None:
    docs: DocumentRepo = cfg["docs"]
    jobs: JobRepo = cfg["jobs"]
    audit: AuditRepo = cfg["audit"]

    status = "review_pending" if ctx.needs_review else "completed"

    await docs.set_extraction(ctx.document_id, ctx.extraction_payload)
    await docs.set_status(ctx.document_id, status)

    await jobs.set_status(ctx.job_id, status)
    await jobs.set_outputs(ctx.job_id, ctx.outputs)

    await audit.append(
        ctx.document_id,
        "system",
        "persisted",
        {"status": status, "outputs": ctx.outputs},
        job_id=ctx.job_id,
    )
