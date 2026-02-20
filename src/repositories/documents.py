from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.models import Document
from ..common.time import utcnow

class DocumentRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, document_id: str, content_hash: str = "pending", status: str = "queued") -> Document:
        now = utcnow()
        doc = Document(
            id=document_id,
            content_hash=content_hash,
            status=status,
            received_at=now,
            updated_at=now,
            extraction_json={},
            locked_fields={},
        )
        self.session.add(doc)
        return doc

    async def get(self, document_id: str) -> Document | None:
        return await self.session.get(Document, document_id)

    async def set_status(self, document_id: str, status: str) -> None:
        doc = await self.session.get(Document, document_id)
        if not doc:
            raise KeyError("document_not_found")
        doc.status = status
        doc.updated_at = utcnow()

    async def set_extraction(self, document_id: str, extraction: dict) -> None:
        doc = await self.session.get(Document, document_id)
        if not doc:
            raise KeyError("document_not_found")
        doc.extraction_json = extraction
        doc.updated_at = utcnow()

    async def merge_locked_fields(self, document_id: str, locked: dict) -> None:
        doc = await self.session.get(Document, document_id)
        if not doc:
            raise KeyError("document_not_found")
        doc.locked_fields = {**(doc.locked_fields or {}), **(locked or {})}
        doc.updated_at = utcnow()
