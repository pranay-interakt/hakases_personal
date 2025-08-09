def chunk_text(text: str, size: int = 2500, overlap: int = 300):
    chunks, i, n, idx = [], 0, len(text), 0
    while i < n:
        j = min(n, i + size)
        chunks.append({"id": idx, "text": text[i:j]})
        idx += 1
        i = j - overlap
        if i <= 0: i = j
    return chunks
