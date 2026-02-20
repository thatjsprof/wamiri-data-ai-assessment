from __future__ import annotations

import asyncio
import random
import time
import yaml

from .graph import StepSpec, WorkflowGraph
from .context import WorkflowContext
from .rate_limit import AsyncTokenBucket
from .steps.registry import get as get_step

# Import steps so they register
from .steps import ocr as _ocr  # noqa: F401
from .steps import llm_extract as _llm  # noqa: F401
from .steps import normalize_line_items as _norm  # noqa: F401
from .steps import validate as _val  # noqa: F401
from .steps import write_outputs as _out  # noqa: F401
from .steps import persist as _persist  # noqa: F401
from .steps import review_gate as _review  # noqa: F401


def _jitter(seconds: float) -> float:
    return seconds * (0.5 + random.random())


class WorkflowRunner:
    def __init__(self, cfg_path: str = "configs/workflow.yaml"):
        raw = yaml.safe_load(open(cfg_path, "r", encoding="utf-8"))
        steps_cfg = raw["workflow"]["steps"]

        self.step_cfg = steps_cfg
        steps = {}
        for name, s in steps_cfg.items():
            steps[name] = StepSpec(
                name=name,
                kind=s["kind"],
                depends_on=s.get("depends_on", []),
                retries=int(s.get("retries", 0)),
                rate_limit_rps=s.get("rate_limit_rps"),
                rate_limit_burst=s.get("rate_limit_burst"),
                max_concurrency=s.get("max_concurrency"),
            )

        self.graph = WorkflowGraph(steps)
        self.graph.validate()

        # Rate limiters per step name (simple + explicit)
        self.limiters: dict[str, AsyncTokenBucket] = {}
        for name, spec in steps.items():
            if spec.rate_limit_rps and spec.rate_limit_burst:
                self.limiters[name] = AsyncTokenBucket(spec.rate_limit_rps, spec.rate_limit_burst)

    async def run(self, ctx: WorkflowContext, injected_cfg: dict) -> None:
        layers = self.graph.topological_layers()

        for layer in layers:
            await asyncio.gather(*[self._run_step(step_name, ctx, injected_cfg) for step_name in layer])

    async def _run_step(self, step_name: str, ctx: WorkflowContext, injected_cfg: dict) -> None:
        spec = self.graph.steps[step_name]
        fn = get_step(spec.kind)
        cfg = dict(self.step_cfg[step_name])
        cfg.update(injected_cfg)  # inject repos/session

        limiter = self.limiters.get(step_name)
        attempts = max(1, spec.retries + 1)

        for i in range(attempts):
            if limiter:
                await limiter.take(1.0)

            try:
                await fn(ctx, cfg)
                return
            except Exception:
                if i == attempts - 1:
                    raise
                await asyncio.sleep(_jitter(min(6.0, 0.5 * (2 ** i))))
