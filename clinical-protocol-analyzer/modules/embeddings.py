from __future__ import annotations
from typing import List
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class VectorIndex:
    def __init__(self, model_name: str, index_path: str, batch_size: int = 64, device: str = "cpu"):
        self.model = SentenceTransformer(model_name, device=device)
        self.index_path = index_path
        self.batch_size = batch_size
        self.index = None
        self.ids = []

    def build(self, texts: List[str]):
        embs = self._embed_batch(texts)
        d = embs.shape[1]
        self.index = faiss.IndexFlatIP(d)
        faiss.normalize_L2(embs)
        self.index.add(embs)
        self.ids = list(range(len(texts)))
        self._save()

    def _embed_batch(self, texts: List[str]) -> np.ndarray:
        vectors = self.model.encode(texts, batch_size=self.batch_size, show_progress_bar=False, normalize_embeddings=True)
        return np.array(vectors, dtype="float32")

    def _save(self):
        os.makedirs(self.index_path, exist_ok=True)
        faiss.write_index(self.index, os.path.join(self.index_path, "index.faiss"))
        with open(os.path.join(self.index_path, "ids.txt"), "w") as f:
            f.write("\n".join(map(str, self.ids)))

    def load(self):
        self.index = faiss.read_index(os.path.join(self.index_path, "index.faiss"))
        with open(os.path.join(self.index_path, "ids.txt"), "r") as f:
            self.ids = [int(x.strip()) for x in f if x.strip()]

    def search(self, queries: List[str], k: int = 8):
        q_embs = self._embed_batch(queries)
        faiss.normalize_L2(q_embs)
        scores, idxs = self.index.search(q_embs, k)
        return scores, idxs
