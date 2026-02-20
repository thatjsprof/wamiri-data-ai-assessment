from __future__ import annotations
from datetime import timedelta
import uuid
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import ReviewItem
from ..common.time import utcnow


class ReviewQueueRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _priority(self, deadline) -> int:
        mins = max(0, int((deadline - utcnow()).total_seconds() / 60))
        if mins <= 30:
            return 100
        if mins <= 60:
            return 80
        if mins <= 120:
            return 60
        return 40

    async def create(
        self,
        document_id: str,
        job_id: str,
        reason: str,
        extraction_json: dict,
        locked_fields: dict,
        sla_minutes: int = 240,
    ) -> ReviewItem:
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

    async def list_pending(
        self, limit: int, offset: int, user: str | None = None
    ) -> list[ReviewItem]:
        """List pending items, or if user provided, include their claimed items too."""
        if user:
            # Show pending + claimed by this user
            q = (
                select(ReviewItem)
                .where(
                    (ReviewItem.status == "pending")
                    | (
                        (ReviewItem.status == "claimed")
                        & (ReviewItem.assigned_to == user)
                    )
                )
                .order_by(ReviewItem.priority.desc(), ReviewItem.sla_deadline.asc())
                .limit(limit)
                .offset(offset)
            )
        else:
            # Only pending
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
        sql = text(
            """
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
        """
        )
        res = await self.session.execute(sql, {"user": user})
        row = res.mappings().first()
        if not row:
            return None
        return await self.session.get(ReviewItem, row["id"])

    async def get(self, review_id: str) -> ReviewItem | None:
        return await self.session.get(ReviewItem, review_id)

    async def submit(
        self,
        review_id: str,
        decision: str,
        user: str,
        corrections: dict,
        reject_reason: str | None,
    ) -> ReviewItem:
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

    async def stats_for_dashboard(self) -> dict:
        """Return stats for the review dashboard: queue depth, reviewed today, avg review time, SLA compliance."""
        now = utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        window_24h = now - timedelta(hours=24)

        # Queue depth (pending only)
        q_depth = (
            select(func.count())
            .select_from(ReviewItem)
            .where(ReviewItem.status == "pending")
        )
        depth_res = await self.session.execute(q_depth)
        queue_depth = int(depth_res.scalar() or 0)

        # Reviewed today (completed or rejected with completed_at >= today_start)
        q_today = (
            select(func.count())
            .select_from(ReviewItem)
            .where(
                ReviewItem.status.in_(["completed", "rejected"]),
                ReviewItem.completed_at >= today_start,
            )
        )
        today_res = await self.session.execute(q_today)
        reviewed_today = int(today_res.scalar() or 0)

        # Average review time (seconds) for items completed in last 24h with both claimed_at and completed_at
        q_avg = (
            select(
                func.avg(
                    func.extract(
                        "epoch", ReviewItem.completed_at - ReviewItem.claimed_at
                    )
                )
            )
            .select_from(ReviewItem)
            .where(
                ReviewItem.status.in_(["completed", "rejected"]),
                ReviewItem.completed_at >= window_24h,
                ReviewItem.claimed_at.isnot(None),
                ReviewItem.completed_at.isnot(None),
            )
        )
        avg_res = await self.session.execute(q_avg)
        avg_seconds = float(avg_res.scalar() or 0)

        # SLA compliance: % of items completed in last 24h where completed_at <= sla_deadline
        q_total = (
            select(func.count())
            .select_from(ReviewItem)
            .where(
                ReviewItem.status.in_(["completed", "rejected"]),
                ReviewItem.completed_at >= window_24h,
                ReviewItem.completed_at.isnot(None),
            )
        )
        q_ontime = (
            select(func.count())
            .select_from(ReviewItem)
            .where(
                ReviewItem.status.in_(["completed", "rejected"]),
                ReviewItem.completed_at >= window_24h,
                ReviewItem.completed_at <= ReviewItem.sla_deadline,
            )
        )
        total_res = await self.session.execute(q_total)
        ontime_res = await self.session.execute(q_ontime)
        total_24h = int(total_res.scalar() or 0)
        ontime_24h = int(ontime_res.scalar() or 0)
        sla_compliance_pct = (ontime_24h / total_24h * 100.0) if total_24h else 100.0

        return {
            "queue_depth": queue_depth,
            "reviewed_today": reviewed_today,
            "avg_review_time_seconds": round(avg_seconds, 1),
            "sla_compliance_pct": round(sla_compliance_pct, 1),
        }
