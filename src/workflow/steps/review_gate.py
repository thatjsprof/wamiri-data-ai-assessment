from __future__ import annotations

from .registry import register
from ..context import WorkflowContext
from ...repositories.review_queue import ReviewQueueRepo
from ...repositories.jobs import JobRepo
from ...repositories.audit import AuditRepo


@register("review_gate")
async def run(ctx: WorkflowContext, cfg: dict) -> None:
    if not ctx.needs_review:
        return

    review: ReviewQueueRepo = cfg["review"]
    jobs: JobRepo = cfg["jobs"]
    audit: AuditRepo = cfg["audit"]

    item = await review.create(
        document_id=ctx.document_id,
        job_id=ctx.job_id,
        reason="validation_failed_or_low_confidence",
        extraction_json=ctx.extraction_payload,
        locked_fields=ctx.locked_fields,
    )
    await jobs.set_review_item(ctx.job_id, item.id)
    await audit.append(
        ctx.document_id,
        "system",
        "review_enqueued",
        {"review_item_id": item.id},
        job_id=ctx.job_id,
    )
