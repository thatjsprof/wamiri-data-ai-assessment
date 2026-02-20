from __future__ import annotations
from typing import Iterable

def textract_blocks_to_text(blocks: list[dict]) -> str:
    lines = []
    for b in blocks:
        if b.get("BlockType") == "LINE" and b.get("Text"):
            lines.append(b["Text"])
    return "\n".join(lines).strip()
