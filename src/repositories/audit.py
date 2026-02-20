from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.models import AuditLog
from ..common.time import utcnow

class AuditRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def append(self, document_id: str, actor: str, action: str, details: dict, job_id: str | None = None) -> None:
        self.session.add(AuditLog(
            document_id=document_id,
            job_id=job_id,
            at=utcnow(),
            actor=actor,
            action=action,
            details=details or {},
        ))
