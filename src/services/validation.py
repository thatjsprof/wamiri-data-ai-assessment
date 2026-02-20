from __future__ import annotations
from datetime import datetime
from typing import List, Dict, Any
import yaml


class InvoiceValidator:
    def __init__(self, cfg_path: str = "configs/extraction_module_schema.yaml"):
        cfg = yaml.safe_load(open(cfg_path, "r", encoding="utf-8"))
        self.required = cfg["validation"]["required_fields"]
        self.supported = set(cfg["validation"]["supported_currencies"])

        conf_cfg = cfg.get("confidence", {})
        self.default_threshold = float(conf_cfg.get("default_threshold", 0.75))
        self.field_thresholds = conf_cfg.get("field_thresholds", {})

    def validate(
        self, fields: dict, field_confidence: Dict[str, float] | None = None
    ) -> List[str]:
        """Validate fields and check confidence thresholds."""
        errs: List[str] = []
        confidence = field_confidence or {}

        for k in self.required:
            if k not in fields or fields[k] in (None, "", "UNKNOWN"):
                errs.append(f"missing_required:{k}")

        total_amt = fields.get("total_amount")
        if total_amt is not None and total_amt != "":
            try:
                if float(total_amt) < 0:
                    errs.append("total_non_negative")
            except (ValueError, TypeError):
                errs.append("invalid_total_amount")

        currency = fields.get("currency")
        if currency and currency not in (None, "", "UNKNOWN"):
            if currency not in self.supported:
                errs.append("currency_unsupported")

        invoice_date = fields.get("invoice_date")
        if invoice_date and invoice_date not in (None, "", "UNKNOWN"):
            try:
                datetime.fromisoformat(invoice_date)
            except (ValueError, TypeError):
                errs.append("invalid_invoice_date")

        for field_name in self.required:
            if field_name in fields and fields[field_name] not in (None, "", "UNKNOWN"):
                threshold = float(
                    self.field_thresholds.get(field_name, self.default_threshold)
                )
                field_conf = confidence.get(field_name, 0.0)
                if field_conf < threshold:
                    errs.append(
                        f"low_confidence:{field_name}:{field_conf:.2f}<{threshold:.2f}"
                    )

        return errs
