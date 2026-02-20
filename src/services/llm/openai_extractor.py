from __future__ import annotations
from typing import Any, Dict
import json
from pydantic import BaseModel

from openai import OpenAI
from ...settings import settings


class InvoiceFields(BaseModel):
    invoice_number: str
    vendor_name: str
    total_amount: float
    currency: str
    invoice_date: str
    tax_amount: float | None = None
    line_items: list[dict] | None = None


class OpenAIStructuredExtractor:
    def __init__(self):
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not set.")
        self.client = OpenAI(api_key=settings.openai_api_key)

    def extract(self, text: str) -> dict:
        schema = InvoiceFields.model_json_schema()
        resp = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "Extract invoice fields from text. Return ONLY valid JSON.",
                },
                {"role": "user", "content": text[:20000]},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "InvoiceFields", "schema": schema},
            },
            temperature=0,
        )
        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)
        validated = InvoiceFields(**data)
        return validated.model_dump()
