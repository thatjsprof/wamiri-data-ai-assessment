from __future__ import annotations

import asyncio
from .registry import register
from ..context import WorkflowContext
from ...services.ocr.textract_extractor import TextractTextExtractor


@register("ocr")
async def run(ctx: WorkflowContext, cfg: dict) -> None:
    extractor = TextractTextExtractor()
    ctx.text = await asyncio.to_thread(extractor.extract_text, ctx.file_bytes, ctx.content_type)
