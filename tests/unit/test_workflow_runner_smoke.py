import pytest
import asyncio
from src.workflow.graph import StepSpec, WorkflowGraph
from src.workflow.context import WorkflowContext

@pytest.mark.asyncio
async def test_runner_like_execution_order():
    # Minimal check of layering works; we don't invoke real steps here.
    steps = {
        "a": StepSpec(name="a", kind="a", depends_on=[]),
        "b": StepSpec(name="b", kind="b", depends_on=["a"]),
        "c": StepSpec(name="c", kind="c", depends_on=["a"]),
        "d": StepSpec(name="d", kind="d", depends_on=["b","c"]),
    }
    g = WorkflowGraph(steps)
    g.validate()
    layers = g.topological_layers()
    assert layers[0] == ["a"]
    assert set(layers[1]) == {"b","c"}
    assert layers[2] == ["d"]
