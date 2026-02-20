from src.workflow.graph import StepSpec, WorkflowGraph

def test_cycle_detection():
    steps = {
        "a": StepSpec(name="a", kind="x", depends_on=["b"]),
        "b": StepSpec(name="b", kind="x", depends_on=["a"]),
    }
    g = WorkflowGraph(steps)
    try:
        g.validate()
        assert False, "expected cycle_detected"
    except ValueError as e:
        assert "cycle" in str(e)

def test_topological_layers():
    steps = {
        "ocr": StepSpec(name="ocr", kind="ocr", depends_on=[]),
        "extract": StepSpec(name="extract", kind="llm", depends_on=["ocr"]),
        "validate": StepSpec(name="validate", kind="val", depends_on=["extract"]),
    }
    g = WorkflowGraph(steps)
    g.validate()
    layers = g.topological_layers()
    assert layers[0] == ["ocr"]
    assert "extract" in layers[1]
