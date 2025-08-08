from __future__ import annotations
from typing import List, Dict
import re

def _split_by_delimiters(text: str, size: int, overlap: int) -> List[str]:
    # Try to respect headings; fallback to paragraphs/sentences
    blocks = re.split(r"\n(?=[A-Z][A-Z0-9 ._-]{4,}\n)", text)
    if len(blocks) == 1:
        blocks = text.split("\n\n")
    chunks = []
    for block in blocks:
        if len(block) <= size:
            chunks.append(block)
            continue
        sentences = re.split(r"(?<=[.!?])\s+", block)
        buff = ""
        for s in sentences:
            if len(buff) + len(s) + 1 <= size:
                buff += (s + " ")
            else:
                if buff:
                    chunks.append(buff.strip())
                buff = s + " "
        if buff:
            chunks.append(buff.strip())
    with_overlap = []
    for i, ch in enumerate(chunks):
        if i == 0:
            with_overlap.append(ch)
            continue
        prev = chunks[i-1]
        tail = prev[-overlap:]
        combined = (tail + ch)[- (size + overlap):]
        with_overlap.append(combined)
    return [c.strip() for c in with_overlap if c.strip()]

def chunk_text(text: str, size: int = 2500, overlap: int = 300) -> List[Dict]:
    parts = _split_by_delimiters(text, size=size, overlap=overlap)
    return [{"id": i, "text": p} for i, p in enumerate(parts)]
