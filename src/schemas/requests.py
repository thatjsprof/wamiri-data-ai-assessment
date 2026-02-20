from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class SubmitReviewRequest(BaseModel):
    decision: Literal["approve", "correct", "reject"]
    user: str = "reviewer_1"
    corrections: Dict[str, Any] = Field(default_factory=dict)
    reject_reason: Optional[str] = None
