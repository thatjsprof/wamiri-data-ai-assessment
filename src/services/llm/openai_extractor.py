from __future__ import annotations

import json
from pydantic import BaseModel, Field, ValidationError

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

        system_prompt = (
            "You extract invoice fields from raw OCR text.\n\n"
            "Rules:\n"
            "- Output must be ONLY valid JSON that matches the schema.\n"
            "- Do not guess. Use null only for optional fields (tax_amount, line_items).\n"
            "- invoice_number: the invoice/reference number.\n"
            "- vendor_name: the supplier/company issuing the invoice.\n"
            "- total_amount: the final payable amount. Prefer labels like 'Total', 'Amount Due', 'Balance Due'.\n"
            "- currency: a 3-letter ISO code (e.g., USD, EUR, GBP, NGN). If multiple appear, pick the one tied to total.\n"
            "- invoice_date: convert to YYYY-MM-DD if the date is present. If unclear, pick the clearest invoice date.\n"
            "- tax_amount: only if explicitly shown (VAT, Tax, GST). Otherwise null.\n"
            "- line_items: include only if line items are clearly present; otherwise null.\n"
            "- Ignore duplicates, headers/footers, and OCR noise.\n"
        )

        resp = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text[:20000]},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "InvoiceFields", "schema": schema},
            },
            temperature=0,
        )

        content = resp.choices[0].message.content or "{}"

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = {}

        try:
            validated = InvoiceFields(**data)
        except ValidationError as e:
            raise RuntimeError(
                f"OpenAI extraction returned invalid payload: {e}"
            ) from e

        return validated.model_dump()
