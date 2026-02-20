from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass(frozen=True)
class StepSpec:
    name: str
    kind: str
    depends_on: List[str]
    retries: int = 0
    rate_limit_rps: float | None = None
    rate_limit_burst: int | None = None
    max_concurrency: int | None = None


class WorkflowGraph:
    def __init__(self, steps: Dict[str, StepSpec]):
        self.steps = steps

    def validate(self) -> None:
        # Check references
        for name, spec in self.steps.items():
            for dep in spec.depends_on:
                if dep not in self.steps:
                    raise ValueError(f"unknown_dependency:{name}->{dep}")
        # Cycle detection
        visiting: Set[str] = set()
        visited: Set[str] = set()

        def dfs(n: str):
            if n in visiting:
                raise ValueError("cycle_detected")
            if n in visited:
                return
            visiting.add(n)
            for d in self.steps[n].depends_on:
                dfs(d)
            visiting.remove(n)
            visited.add(n)

        for n in self.steps:
            dfs(n)

    def topological_layers(self) -> List[List[str]]:
        # Kahn's algorithm but grouped into layers for parallel execution
        remaining_deps = {n: set(s.depends_on) for n, s in self.steps.items()}
        ready = sorted([n for n, deps in remaining_deps.items() if not deps])
        layers: List[List[str]] = []

        while ready:
            layer = ready
            layers.append(layer)
            ready = []
            for n in layer:
                for m, deps in remaining_deps.items():
                    deps.discard(n)
            for n, deps in remaining_deps.items():
                if n not in sum(layers, []) and not deps:
                    ready.append(n)
            ready = sorted(list(set(ready)))

        if sum(len(x) for x in layers) != len(self.steps):
            raise ValueError("cycle_or_missing_nodes")
        return layers
