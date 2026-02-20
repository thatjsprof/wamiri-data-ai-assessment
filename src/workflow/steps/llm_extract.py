from __future__ import annotations

import asyncio
from .registry import register
from ..context import WorkflowContext
from ...services.llm.openai_extractor import OpenAIStructuredExtractor


@register("llm_extract")
async def run(ctx: WorkflowContext, cfg: dict) -> None:
    extractor = OpenAIStructuredExtractor()
    result = await asyncio.to_thread(extractor.extract, ctx.text or "")

    if isinstance(result, dict) and "fields" in result:
        extracted_fields = result["fields"]
        ctx.field_confidence = result.get("confidence", {})
    else:
        extracted_fields = result
        ctx.field_confidence = {}

    locked = ctx.locked_fields or {}
    ctx.fields = {**extracted_fields, **locked}

    for field_name in locked:
        ctx.field_confidence[field_name] = 0.99
