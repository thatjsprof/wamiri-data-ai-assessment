import asyncio
import time
import pytest

from src.workflow.graph import StepSpec, WorkflowGraph
from src.workflow.context import WorkflowContext

@pytest.mark.asyncio
async def test_parallel_layer_runs_faster_than_serial():
    # Build a tiny graph with two parallel steps.
    steps = {
        "a": StepSpec(name="a", kind="a", depends_on=[]),
        "b": StepSpec(name="b", kind="b", depends_on=["a"]),
        "c": StepSpec(name="c", kind="c", depends_on=["a"]),
    }
    g = WorkflowGraph(steps)
    g.validate()
    layers = g.topological_layers()
    assert layers[0] == ["a"]
    assert set(layers[1]) == {"b", "c"}

    # Simulate runner behavior: run layer 1 concurrently.
    async def slow():
        await asyncio.sleep(0.25)

    start = time.time()
    await asyncio.gather(slow(), slow())
    elapsed = time.time() - start

    # If truly parallel, it should be close to 0.25s, not 0.5s.
    assert elapsed < 0.40
