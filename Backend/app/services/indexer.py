from app.db.session import SessionLocal
from app.db import models
from app.services.embeddings import EmbeddingService
from app.services.index import FaissIndex

class IndexerService:

    def __init__(self):
        self.embedder = EmbeddingService()

    def build_index(self, user_id: int):

        db = SessionLocal()

        try:
            chunks = db.query(models.Chunk).join(models.Document).filter(
                models.Document.user_id == user_id
            ).all()

            texts = [c.content for c in chunks]
            ids = [c.id for c in chunks]

        finally:
            db.close()

        if not texts:
            # Create an empty index to clear it out when all docs are deleted
            index = FaissIndex(user_id=user_id, dim=384)
            index.save()
            return {"message": "No chunks to index. Cleared FAISS index."}

        # 🔥 create a fresh index every time
        index = FaissIndex(user_id=user_id, dim=384)

        vectors = self.embedder.embed_texts(texts)

        index.add(vectors, ids)

        index.save()

        return {
            "num_chunks_indexed": len(texts),
            "dim": vectors.shape[1]
        }