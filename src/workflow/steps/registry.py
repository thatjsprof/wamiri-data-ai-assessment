from __future__ import annotations

from typing import Callable, Dict, Awaitable
from ..context import WorkflowContext

StepFn = Callable[[WorkflowContext, dict], Awaitable[None]]

_REGISTRY: Dict[str, StepFn] = {}

def register(kind: str):
    def deco(fn: StepFn):
        _REGISTRY[kind] = fn
        return fn
    return deco

def get(kind: str) -> StepFn:
    if kind not in _REGISTRY:
        raise KeyError(f"unknown_step_kind:{kind}")
    return _REGISTRY[kind]
