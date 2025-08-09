import numpy as np
from sentence_transformers import SentenceTransformer
try:
    import faiss
except Exception:
    faiss = None
class VectorIndex:
    def __init__(self, model_name: str, index_path: str, batch_size: int = 64, device: str = "cpu"):
        self.model = SentenceTransformer(model_name, device=device)
        self.index = None
    def build(self, texts):
        embs = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        embs = np.asarray(embs, dtype="float32")
        if faiss:
            self.index = faiss.IndexFlatIP(embs.shape[1]); self.index.add(embs)
        else:
            self.index = embs
        self.texts = texts
    def load(self): pass
    def search(self, queries, k=8):
        q = self.model.encode(queries, normalize_embeddings=True, show_progress_bar=False)
        q = np.asarray(q, dtype="float32")
        if hasattr(self.index, "search"):
            D, I = self.index.search(q, k); return D, I
        sims = q @ self.index.T
        I = sims.argsort(axis=1)[:, ::-1][:, :k]
        D = np.take_along_axis(sims, I, axis=1)
        return D, I
