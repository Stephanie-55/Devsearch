import numpy as np
from app.db.session import SessionLocal
from app.db import models
from app.services.embeddings import EmbeddingService

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

class CompareService:
    def __init__(self):
        self.embedder = EmbeddingService()

    def compare_documents(self, doc_id_a: int, doc_id_b: int, user_id: int, top_k: int = 5):
        db = SessionLocal()
        try:
            doc_a = db.query(models.Document).filter(models.Document.id == doc_id_a, models.Document.user_id == user_id).first()
            doc_b = db.query(models.Document).filter(models.Document.id == doc_id_b, models.Document.user_id == user_id).first()
            if not doc_a or not doc_b:
                return {"message": "One or both documents not found or access denied", "top_matches": [], "similarity": 0}
            
            chunks_a = db.query(models.Chunk).filter(models.Chunk.document_id == doc_id_a).all()
            chunks_b = db.query(models.Chunk).filter(models.Chunk.document_id == doc_id_b).all()
        finally:
            db.close()

        if not chunks_a or not chunks_b:
            return {"message": "One or both documents have no chunks", "top_matches": [], "similarity": 0}

        texts_a = [c.content for c in chunks_a]
        texts_b = [c.content for c in chunks_b]

        vecs_a = self.embedder.embed_texts(texts_a)
        vecs_b = self.embedder.embed_texts(texts_b)

        matches = []
        sims = []

        for i, va in enumerate(vecs_a):
            for j, vb in enumerate(vecs_b):
                sim = cosine_sim(va, vb)
                sims.append(sim)
                matches.append({
                    "chunk_a_id": chunks_a[i].id,
                    "chunk_b_id": chunks_b[j].id,
                    "similarity": sim,
                    "chunk_a_preview": chunks_a[i].content[:150],
                    "chunk_b_preview": chunks_b[j].content[:150],
                })

        matches.sort(key=lambda x: x["similarity"], reverse=True)

        doc_similarity = float(np.mean(sorted(sims, reverse=True)[:top_k]))

        return {
            "doc_a_id": doc_id_a,
            "doc_b_id": doc_id_b,
            "similarity": doc_similarity,
            "top_matches": matches[:top_k]
        }