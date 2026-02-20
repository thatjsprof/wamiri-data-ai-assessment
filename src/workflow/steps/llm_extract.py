from __future__ import annotations

import asyncio
from .registry import register
from ..context import WorkflowContext
from ...services.llm.openai_extractor import OpenAIStructuredExtractor


@register("llm_extract")
async def run(ctx: WorkflowContext, cfg: dict) -> None:
    extractor = OpenAIStructuredExtractor()
    fields = await asyncio.to_thread(extractor.extract, ctx.text or "")
    # Apply locked fields (human overrides)
    ctx.fields = {**fields, **(ctx.locked_fields or {})}
