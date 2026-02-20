from __future__ import annotations
from datetime import timedelta
import uuid
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import ReviewItem
from ..common.time import utcnow

class ReviewQueueRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _priority(self, deadline) -> int:
        mins = max(0, int((deadline - utcnow()).total_seconds() / 60))
        if mins <= 30: return 100
        if mins <= 60: return 80
        if mins <= 120: return 60
        return 40

    async def create(self, document_id: str, job_id: str, reason: str, extraction_json: dict, locked_fields: dict, sla_minutes: int = 240) -> ReviewItem:
        rid = str(uuid.uuid4())
        deadline = utcnow() + timedelta(minutes=sla_minutes)
        item = ReviewItem(
            id=rid,
            document_id=document_id,
            job_id=job_id,
            created_at=utcnow(),
            claimed_at=None,
            completed_at=None,
            sla_deadline=deadline,
            priority=self._priority(deadline),
            status="pending",
            assigned_to=None,
            reason=reason,
            extraction_json=extraction_json or {},
            locked_fields=locked_fields or {},
        )
        self.session.add(item)
        return item

    async def list_pending(self, limit: int, offset: int) -> list[ReviewItem]:
        q = (
            select(ReviewItem)
            .where(ReviewItem.status == "pending")
            .order_by(ReviewItem.priority.desc(), ReviewItem.sla_deadline.asc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(q)
        return list(res.scalars().all())

    async def claim_next(self, user: str) -> ReviewItem | None:
        sql = text("""
        WITH next_item AS (
          SELECT id
          FROM review_items
          WHERE status = 'pending'
          ORDER BY priority DESC, sla_deadline ASC
          FOR UPDATE SKIP LOCKED
          LIMIT 1
        )
        UPDATE review_items
        SET status='claimed', assigned_to=:user, claimed_at=NOW()
        WHERE id IN (SELECT id FROM next_item)
        RETURNING id;
        """)
        res = await self.session.execute(sql, {"user": user})
        row = res.mappings().first()
        if not row:
            return None
        return await self.session.get(ReviewItem, row["id"])

    async def get(self, review_id: str) -> ReviewItem | None:
        return await self.session.get(ReviewItem, review_id)

    async def submit(self, review_id: str, decision: str, user: str, corrections: dict, reject_reason: str | None) -> ReviewItem:
        item = await self.session.get(ReviewItem, review_id)
        if not item:
            raise KeyError("review_not_found")

        if decision in ("approve", "correct"):
            item.status = "completed"
            item.assigned_to = user
            item.completed_at = utcnow()
            if corrections:
                item.locked_fields = {**(item.locked_fields or {}), **corrections}
        else:
            item.status = "rejected"
            item.assigned_to = user
            item.completed_at = utcnow()
            if reject_reason:
                item.reason = f"{item.reason} | rejected_reason={reject_reason}"

        return item
