from sentence_transformers import SentenceTransformer
import numpy as np

# Global cache so we don't reload PyTorch weights on every request
_MODEL_CACHE = {}

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if model_name not in _MODEL_CACHE:
            _MODEL_CACHE[model_name] = SentenceTransformer(
                model_name,
                local_files_only=True
            )
        self.model = _MODEL_CACHE[model_name]

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        vec = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        return vec

    def embed_documents(self, texts: list[str]):

        vecs = self.model.encode(texts)

        return np.array(vecs).astype("float32")