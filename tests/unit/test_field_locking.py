import asyncio
import pytest

from src.workflow.context import WorkflowContext
from src.workflow.steps.llm_extract import run as llm_step

class _FakeExtractor:
    def extract(self, text: str):
        return {"vendor_name": "ACME", "total_amount": 100, "currency": "USD"}

@pytest.mark.asyncio
async def test_locked_fields_override_llm_result(monkeypatch):
    # Monkeypatch only inside the test. Production still uses real OpenAI.
    from src.services.llm import openai_extractor as mod
    monkeypatch.setattr(mod, "OpenAIStructuredExtractor", lambda: _FakeExtractor())

    ctx = WorkflowContext(
        job_id="j",
        document_id="d",
        content_type="application/pdf",
        file_bytes=b"x",
        locked_fields={"total_amount": 999},
        text="hello",
    )
    await llm_step(ctx, cfg={})
    assert ctx.fields["vendor_name"] == "ACME"
    assert ctx.fields["total_amount"] == 999
