from PyPDF2 import PdfReader
from docx import Document
import os, re
def load_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        r = PdfReader(path); return "\n".join((p.extract_text() or "") for p in r.pages)
    if ext == ".docx":
        d = Document(path); return "\n".join(p.text for p in d.paragraphs)
    return open(path, "r", encoding="utf-8", errors="ignore").read()
def clean_text(text: str) -> str:
    text = re.sub(r"\r", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
