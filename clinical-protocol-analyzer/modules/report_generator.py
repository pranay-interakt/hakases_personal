# modules/report_generator.py
from __future__ import annotations
from typing import Dict, Any
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

def to_markdown(narrative_md: str) -> str:
    return narrative_md

def md_to_pdf(md_text: str, pdf_path: str):
    c = canvas.Canvas(pdf_path, pagesize=LETTER)
    width, height = LETTER
    y = height - 50
    for line in md_text.splitlines():
        if y < 50:
            c.showPage(); y = height - 50
        c.drawString(50, y, line[:120])
        y -= 14
    c.save()

