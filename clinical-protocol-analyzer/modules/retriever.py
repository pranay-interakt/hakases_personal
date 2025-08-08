from __future__ import annotations
from typing import List, Dict
from .embeddings import VectorIndex

class Retriever:
    def __init__(self, index: VectorIndex, chunks: List[Dict]):
        self.index = index
        self.chunks = chunks

    @classmethod
    def build(cls, chunks: List[Dict], index_path: str, emb_model: str, batch_size: int = 64, device: str = "cpu"):
        texts = [c["text"] for c in chunks]
        index = VectorIndex(model_name=emb_model, index_path=index_path, batch_size=batch_size, device=device)
        index.build(texts)
        return cls(index=index, chunks=chunks)

    @classmethod
    def load(cls, chunks: List[Dict], index_path: str, emb_model: str, batch_size: int = 64, device: str = "cpu"):
        index = VectorIndex(model_name=emb_model, index_path=index_path, batch_size=batch_size, device=device)
        index.load()
        return cls(index=index, chunks=chunks)

    def retrieve(self, query: str, k: int = 8) -> List[Dict]:
        _, idxs = self.index.search([query], k=k)
        hits = idxs[0].tolist()
        return [self.chunks[i] for i in hits]
