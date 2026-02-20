from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.engine import get_session
from ..repositories.review_queue import ReviewQueueRepo
from ..repositories.documents import DocumentRepo
from ..repositories.audit import AuditRepo
from ..observability.metrics import REVIEW_QUEUE_DEPTH
from ..schemas.requests import SubmitReviewRequest
from ..schemas.responses import ClaimResponse, ReviewStatsResponse

router = APIRouter(tags=["review"])


@router.get("/queue/stats", response_model=ReviewStatsResponse)
async def queue_stats(session: AsyncSession = Depends(get_session)):
    """Dashboard stats: queue depth, reviewed today, average review time, SLA compliance."""
    repo = ReviewQueueRepo(session)
    return await repo.stats_for_dashboard()


@router.get("/queue")
async def list_queue(
    limit: int = 50,
    offset: int = 0,
    user: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List queue items. If user provided, includes their claimed items."""
    repo = ReviewQueueRepo(session)
    items = await repo.list_pending(limit=limit, offset=offset, user=user)
    REVIEW_QUEUE_DEPTH.set(len([i for i in items if i.status == "pending"]))

    return {
        "items": [
            {
                "id": i.id,
                "document_id": i.document_id,
                "job_id": i.job_id,
                "created_at": i.created_at,
                "sla_deadline": i.sla_deadline,
                "priority": i.priority,
                "status": i.status,
                "assigned_to": i.assigned_to,
                "reason": i.reason,
                "extraction": i.extraction_json,
                "locked_fields": i.locked_fields,
            }
            for i in items
        ]
    }


@router.post("/queue/claim", response_model=ClaimResponse)
async def claim_next(
    user: str = "reviewer_1", session: AsyncSession = Depends(get_session)
):
    repo = ReviewQueueRepo(session)
    item = await repo.claim_next(user=user)
    await session.commit()

    if not item:
        return ClaimResponse(review_item=None)

    return ClaimResponse(
        review_item={
            "id": item.id,
            "document_id": item.document_id,
            "job_id": item.job_id,
            "sla_deadline": item.sla_deadline,
            "priority": item.priority,
            "status": item.status,
            "assigned_to": item.assigned_to,
            "extraction": item.extraction_json,
            "locked_fields": item.locked_fields,
            "reason": item.reason,
        }
    )


@router.post("/queue/{review_id}/submit")
async def submit(
    review_id: str,
    payload: SubmitReviewRequest,
    session: AsyncSession = Depends(get_session),
):
    queue_repo = ReviewQueueRepo(session)
    docs = DocumentRepo(session)
    audit = AuditRepo(session)

    item = await queue_repo.submit(
        review_id=review_id,
        decision=payload.decision,
        user=payload.user,
        corrections=payload.corrections,
        reject_reason=payload.reject_reason,
    )

    if payload.decision in ("approve", "correct") and payload.corrections:
        await docs.merge_locked_fields(item.document_id, payload.corrections)
        await audit.append(
            item.document_id,
            payload.user,
            "review_completed",
            {
                "decision": payload.decision,
                "corrections": list(payload.corrections.keys()),
            },
            job_id=item.job_id,
        )
    else:
        await audit.append(
            item.document_id,
            payload.user,
            "review_submitted",
            {"decision": payload.decision, "reason": payload.reject_reason},
            job_id=item.job_id,
        )

    await session.commit()
    return {
        "ok": True,
        "review_item_id": item.id,
        "document_id": item.document_id,
        "job_id": item.job_id,
        "status": item.status,
        "locked_fields": item.locked_fields,
    }
