from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["documents"])


@router.get("/documents/{document_id}/preview")
async def document_preview(document_id: str):
    """
    Document preview for the review dashboard.
    Original file bytes are not persisted by default; this endpoint returns 404
    so the UI can show a clear message. To enable preview, persist uploads
    (e.g. to S3 or disk) and serve them here.
    """
    raise HTTPException(
        status_code=404,
        detail="Document preview not stored. Enable file persistence to serve previews.",
    )
