from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class WorkflowContext:
    # Inputs
    job_id: str
    document_id: str
    content_type: str
    file_bytes: bytes

    # Produced state
    text: Optional[str] = None
    fields: Dict[str, Any] = field(default_factory=dict)
    validation_errors: list[str] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    needs_review: bool = False

    # Persisted state
    locked_fields: Dict[str, Any] = field(default_factory=dict)

    # Final extraction payload (written to DB and to disk)
    extraction_payload: Dict[str, Any] = field(default_factory=dict)
