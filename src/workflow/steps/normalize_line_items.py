from __future__ import annotations

import asyncio
from .registry import register
from ..context import WorkflowContext


def _normalize_one(item: dict) -> dict:
    # Keep it simple: standardize a few common keys.
    out = dict(item or {})
    if "qty" in out and "quantity" not in out:
        out["quantity"] = out.pop("qty")
    if "unitPrice" in out and "unit_price" not in out:
        out["unit_price"] = out.pop("unitPrice")
    return out


@register("normalize_line_items")
async def run(ctx: WorkflowContext, cfg: dict) -> None:
    items = ctx.fields.get("line_items") or []
    if not isinstance(items, list) or not items:
        return

    max_c = int(cfg.get("max_concurrency") or 10)
    sem = asyncio.Semaphore(max_c)

    async def worker(it):
        async with sem:
            return await asyncio.to_thread(_normalize_one, it)

    ctx.fields["line_items"] = await asyncio.gather(*[worker(i) for i in items])
