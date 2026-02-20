from src.services.validation import InvoiceValidator

def test_validator_flags_missing():
    v = InvoiceValidator()
    errs = v.validate({"invoice_number":"", "vendor_name":"V", "total_amount": 1, "currency":"USD", "invoice_date":"2025-01-01"})
    assert any(e.startswith("missing_required") for e in errs)

def test_validator_currency():
    v = InvoiceValidator()
    errs = v.validate({"invoice_number":"A","vendor_name":"V","total_amount": 1, "currency":"NGN", "invoice_date":"2025-01-01"})
    assert "currency_unsupported" in errs
