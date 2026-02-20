import pytest
from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_metrics_exists():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "docs_processed_total" in r.text
