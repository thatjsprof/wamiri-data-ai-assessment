from __future__ import annotations
from datetime import datetime
from typing import List
import yaml

class InvoiceValidator:
    def __init__(self, cfg_path: str = "configs/extraction_module_schema.yaml"):
        cfg = yaml.safe_load(open(cfg_path, "r", encoding="utf-8"))
        self.required = cfg["validation"]["required_fields"]
        self.supported = set(cfg["validation"]["supported_currencies"])

    def validate(self, fields: dict) -> List[str]:
        errs: List[str] = []
        for k in self.required:
            if k not in fields or fields[k] in (None, "", "UNKNOWN"):
                errs.append(f"missing_required:{k}")
        try:
            if float(fields.get("total_amount", 0)) < 0:
                errs.append("total_non_negative")
        except Exception:
            errs.append("invalid_total_amount")
        if fields.get("currency") not in self.supported:
            errs.append("currency_unsupported")
        try:
            datetime.fromisoformat(fields.get("invoice_date"))
        except Exception:
            errs.append("invalid_invoice_date")
        return errs
