from __future__ import annotations
from typing import Protocol

class TextExtractor(Protocol):
    def extract_text(self, file_bytes: bytes, content_type: str) -> str: ...

class StructuredExtractor(Protocol):
    def extract(self, text: str) -> dict: ...

class OutputWriter(Protocol):
    def write(self, document_id: str, payload: dict) -> dict: ...
