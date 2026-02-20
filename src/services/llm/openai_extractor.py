from __future__ import annotations

import json
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any

from openai import OpenAI
from ...settings import settings
from ..confidence import compute_all_confidence


class InvoiceFields(BaseModel):
    invoice_number: str | None = None
    vendor_name: str | None = None
    total_amount: float | None = None
    currency: str | None = None
    invoice_date: str | None = None
    tax_amount: float | None = None
    line_items: list[dict] | None = None


class OpenAIStructuredExtractor:
    def __init__(self):
        self.client = (
            OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        )

    def extract(self, text: str) -> Dict[str, Any]:
        def _empty_extraction() -> Dict[str, Any]:
            empty = {
                "invoice_number": None,
                "vendor_name": None,
                "total_amount": None,
                "currency": None,
                "invoice_date": None,
                "tax_amount": None,
                "line_items": None,
            }
            return {
                "fields": empty,
                "confidence": {k: 0.0 for k in empty},
            }

        if not self.client:
            return _empty_extraction()
        try:
            return self._extract_impl(text)
        except Exception:
            return _empty_extraction()

    def _extract_impl(self, text: str) -> Dict[str, Any]:
        assert self.client is not None
        schema = InvoiceFields.model_json_schema()

        system_prompt = (
            "You extract invoice fields from raw OCR text.\n\n"
            "Rules:\n"
            "- Output must be ONLY valid JSON that matches the schema.\n"
            "- If a field is not found or unclear, use null (do not guess or make up values).\n"
            "- invoice_number: the invoice/reference number. Use null if not found.\n"
            "- vendor_name: the supplier/company issuing the invoice. Use null if not found.\n"
            "- total_amount: the final payable amount. Prefer labels like 'Total', 'Amount Due', 'Balance Due'. Use null if not found.\n"
            "- currency: a 3-letter ISO code (e.g., USD, EUR, GBP, CHF). If multiple appear, pick the one tied to total. Use null if not found.\n"
            "- invoice_date: convert to YYYY-MM-DD if the date is present. If unclear or not found, use null.\n"
            "- tax_amount: only if explicitly shown (VAT, Tax, GST). Otherwise null.\n"
            "- line_items: include only if line items are clearly present; otherwise null.\n"
            "- Ignore duplicates, headers/footers, and OCR noise.\n"
            "- It is better to return null for missing fields than to guess incorrect values.\n"
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

        for key in ["invoice_number", "vendor_name", "currency", "invoice_date"]:
            if key in data:
                val = data[key]
                if (
                    val == ""
                    or val == "UNKNOWN"
                    or (isinstance(val, str) and val.strip() == "")
                ):
                    data[key] = None

        try:
            validated = InvoiceFields(**data)
            fields = validated.model_dump()
        except (ValidationError, TypeError, ValueError):

            def _safe_value(key: str):
                v = data.get(key)
                if v is None or v == "" or v == "UNKNOWN":
                    return None
                if key == "total_amount" and not isinstance(v, (int, float)):
                    try:
                        return float(v) if v is not None else None
                    except (TypeError, ValueError):
                        return None
                if (
                    key == "tax_amount"
                    and not isinstance(v, (int, float))
                    and v is not None
                ):
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return None
                if key == "line_items" and not isinstance(v, list):
                    return None
                return v

            fields = {
                "invoice_number": (
                    _safe_value("invoice_number")
                    if isinstance(data.get("invoice_number"), (str, type(None)))
                    else None
                ),
                "vendor_name": (
                    _safe_value("vendor_name")
                    if isinstance(data.get("vendor_name"), (str, type(None)))
                    else None
                ),
                "total_amount": _safe_value("total_amount"),
                "currency": (
                    _safe_value("currency")
                    if isinstance(data.get("currency"), (str, type(None)))
                    else None
                ),
                "invoice_date": (
                    _safe_value("invoice_date")
                    if isinstance(data.get("invoice_date"), (str, type(None)))
                    else None
                ),
                "tax_amount": _safe_value("tax_amount"),
                "line_items": (
                    data.get("line_items")
                    if isinstance(data.get("line_items"), list)
                    else None
                ),
            }

        try:
            confidence_scores = compute_all_confidence(fields, text)
        except Exception:
            confidence_scores = {k: 0.0 for k in fields}

        return {
            "fields": fields,
            "confidence": confidence_scores,
        }
