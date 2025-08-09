from .embeddings import VectorIndex
class Retriever:
    def __init__(self, index, chunks): self.index, self.chunks = index, chunks
    @classmethod
    def build(cls, chunks, index_path, emb_model, batch_size=64, device="cpu"):
        texts = [c["text"] for c in chunks]
        idx = VectorIndex(emb_model, index_path, batch_size, device); idx.build(texts)
        return cls(idx, chunks)
    def retrieve(self, query, k=8):
        _, idxs = self.index.search([query], k=k)
        return [self.chunks[i] for i in idxs[0].tolist()]
