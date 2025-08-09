import numpy as np
from sentence_transformers import SentenceTransformer
class Selector:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    def _emb(self, texts):
        v = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.array(v, dtype="float32")
    def top_k(self, query, items, field, k=10):
        if not items: return []
        qv = self._emb([query]); texts=[i.get(field,"") for i in items]; iv=self._emb(texts)
        sims = (qv @ iv.T).flatten(); order = np.argsort(-sims)[:k]
        return [(float(sims[i]), items[i]) for i in order]
