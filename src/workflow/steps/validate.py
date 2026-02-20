from __future__ import annotations

import asyncio
from .registry import register
from ..context import WorkflowContext
from ...services.validation import InvoiceValidator


@register("validate")
async def run(ctx: WorkflowContext, cfg: dict) -> None:
    validator = InvoiceValidator()
    ctx.validation_errors = await asyncio.to_thread(validator.validate, ctx.fields)
    ctx.needs_review = len(ctx.validation_errors) > 0
