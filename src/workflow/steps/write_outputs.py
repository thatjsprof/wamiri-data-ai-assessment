from __future__ import annotations

import asyncio
from .registry import register
from ..context import WorkflowContext
from ...services.output_writer import FileOutputWriter
from ...common.crypto import sha256_bytes


@register("write_outputs")
async def run(ctx: WorkflowContext, cfg: dict) -> None:
    writer = FileOutputWriter(root="outputs")

    payload = {
        "schema_version": "1.0.0",
        "document_id": ctx.document_id,
        "content_hash": sha256_bytes(b"|".join([ctx.document_id.encode("utf-8"), ctx.file_bytes])),
        "fields": ctx.fields,
        "validation_errors": ctx.validation_errors,
        "status": "review_pending" if ctx.needs_review else "completed",
    }

    ctx.extraction_payload = payload
    ctx.outputs = await asyncio.to_thread(writer.write, ctx.document_id, payload)
