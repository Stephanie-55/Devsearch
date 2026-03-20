import faiss
import numpy as np
import os
import json

class FaissIndex:
    def __init__(self, user_id: int, dim: int):
        self.dim = dim
        self.user_id = user_id
        self.index_path = f"data/faiss_{user_id}.index"
        self.meta_path = f"data/faiss_meta_{user_id}.json"
        
        self.index = faiss.IndexFlatL2(dim)
        self.ids = []  # maps index position -> chunk_id

    def add(self, vectors: np.ndarray, ids: list[int]):
        self.index.add(vectors)
        self.ids.extend(ids)

    def search(self, vector: np.ndarray, k: int = 5):
        distances, idxs = self.index.search(vector, k)
        return distances[0], idxs[0]

    def save(self):
        os.makedirs("data", exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w") as f:
            json.dump(self.ids, f)

    def load(self):
        if not os.path.exists(self.index_path) or not os.path.exists(self.meta_path):
            return False
        self.index = faiss.read_index(self.index_path)
        with open(self.meta_path, "r") as f:
            self.ids = json.load(f)
        return True