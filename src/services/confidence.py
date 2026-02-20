from __future__ import annotations
from typing import Dict, Any
import re
from datetime import datetime


def compute_field_confidence(field_name: str, field_value: Any, ocr_text: str = "") -> float:
    """
    Compute confidence score for a single extracted field.
    Since OpenAI doesn't provide confidence, we use heuristics:
    - Presence and format validation
    - Pattern matching against OCR text
    - Value reasonableness
    """
    if field_value is None or field_value == "":
        return 0.0

    value_str = str(field_value).strip()
    if value_str == "UNKNOWN" or value_str == "":
        return 0.0

    # Base confidence from presence
    base = 0.5

    # Field-specific confidence boosters
    if field_name == "invoice_number":
        # Invoice numbers are usually alphanumeric, 3-20 chars
        if re.match(r"^[A-Z0-9\-/]{3,20}$", value_str, re.IGNORECASE):
            base = 0.85
        elif re.match(r"^[A-Z0-9]{2,30}$", value_str, re.IGNORECASE):
            base = 0.75
        # Check if it appears in OCR text (higher confidence)
        if ocr_text and value_str.lower() in ocr_text.lower():
            base = min(0.95, base + 0.1)

    elif field_name == "vendor_name":
        # Vendor names are usually 2-50 chars, mixed case
        if 2 <= len(value_str) <= 50 and not value_str.isdigit():
            base = 0.80
        if ocr_text and value_str.lower() in ocr_text.lower():
            base = min(0.90, base + 0.1)

    elif field_name == "total_amount":
        try:
            amount = float(value_str.replace(",", "").replace("$", "").replace("€", "").replace("£", ""))
            if amount > 0:
                base = 0.90
            elif amount == 0:
                base = 0.70
            else:
                base = 0.30  # Negative amounts are suspicious
        except (ValueError, AttributeError):
            base = 0.40

    elif field_name == "currency":
        # Currency codes are exactly 3 uppercase letters
        if re.match(r"^[A-Z]{3}$", value_str):
            base = 0.95
        elif len(value_str) == 3:
            base = 0.80

    elif field_name == "invoice_date":
        try:
            # Try parsing ISO date
            datetime.fromisoformat(value_str)
            if re.match(r"^\d{4}-\d{2}-\d{2}$", value_str):
                base = 0.90
            else:
                base = 0.75
        except (ValueError, AttributeError):
            base = 0.40

    elif field_name == "tax_amount":
        try:
            amount = float(value_str.replace(",", "").replace("$", "").replace("€", "").replace("£", ""))
            if amount >= 0:
                base = 0.80
            else:
                base = 0.30
        except (ValueError, AttributeError):
            base = 0.50

    elif field_name == "line_items":
        if isinstance(field_value, list) and len(field_value) > 0:
            base = 0.75
        else:
            base = 0.50

    return min(0.99, max(0.0, base))


def compute_all_confidence(fields: Dict[str, Any], ocr_text: str = "") -> Dict[str, float]:
    """Compute confidence scores for all extracted fields."""
    return {
        field_name: compute_field_confidence(field_name, field_value, ocr_text)
        for field_name, field_value in fields.items()
    }
