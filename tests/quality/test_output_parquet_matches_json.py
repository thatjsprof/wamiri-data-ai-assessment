import json
import pandas as pd

from src.services.output_writer import FileOutputWriter

def test_parquet_and_json_have_same_fields(tmp_path):
    writer = FileOutputWriter(root=str(tmp_path))
    payload = {
        "schema_version": "1.0.0",
        "document_id": "doc1",
        "content_hash": "abc",
        "fields": {
            "invoice_number": "INV-1",
            "vendor_name": "ACME",
            "total_amount": 123.45,
            "currency": "USD",
            "line_items": [{"description": "x", "amount": 1.0}],
        },
        "validation_errors": [],
        "status": "completed",
    }

    out = writer.write("doc1", payload)
    json_path = out["json_path"]
    parquet_path = out["parquet_path"]

    loaded = json.loads(open(json_path, "r", encoding="utf-8").read())
    df = pd.read_parquet(parquet_path)

    # Parquet writer flattens "fields" -> top-level columns.
    # Ensure key invoice fields are present.
    assert "invoice_number" in df.columns
    assert "vendor_name" in df.columns
    assert float(df["total_amount"].iloc[0]) == 123.45
    assert loaded["fields"]["invoice_number"] == "INV-1"
