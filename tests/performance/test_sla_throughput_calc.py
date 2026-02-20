import pytest
from datetime import timedelta

from src.monitoring import _parse_window

def test_window_parser():
    assert _parse_window("5m") == timedelta(minutes=5)
    assert _parse_window("1h") == timedelta(hours=1)
