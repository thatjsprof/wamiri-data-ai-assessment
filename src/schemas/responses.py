from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class ProcessResponse(BaseModel):
    job_id: str
    document_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    document_id: str
    status: str
    error: Optional[str] = None
    outputs: dict
    review_item_id: Optional[str] = None
    extraction: Optional[dict] = None


class ClaimResponse(BaseModel):
    review_item: Optional[dict] = None


class ReviewStatsResponse(BaseModel):
    queue_depth: int
    reviewed_today: int
    avg_review_time_seconds: float
    sla_compliance_pct: float
