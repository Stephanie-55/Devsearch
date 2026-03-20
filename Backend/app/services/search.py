from app.services.embeddings import EmbeddingService
from app.services.index import FaissIndex
from app.db.session import SessionLocal
from app.db import models
from app.utils.snippets import make_snippet

from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi

_RERANKER_CACHE = {}

class SearchService:

    def __init__(self, user_id: int):

        self.user_id = user_id
        self.embedder = EmbeddingService()
        self.index = FaissIndex(user_id=user_id, dim=384)

        # Cross-encoder reranker cache
        model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
        if model_name not in _RERANKER_CACHE:
            _RERANKER_CACHE[model_name] = CrossEncoder(model_name)
        
        self.reranker = _RERANKER_CACHE[model_name]

        loaded = self.index.load()
        if not loaded:
            # We don't raise an error anymore because an empty system shouldn't crash on search init.
            pass

    # --------------------------------------------------
    # Normal search (existing endpoint)
    # --------------------------------------------------
    def search(
        self,
        query: str,
        k: int = 5,
        keywords: list[str] | None = None,
        document_ids: list[int] | None = None
    ):

        # Reload index so newly uploaded documents appear
        self.index.load()

        qvec = self.embedder.embed_query(query)

        # Vector search
        distances, idxs = self.index.search(qvec, k=50)

        db = SessionLocal()

        try:

            candidates = []

            for score, pos in zip(distances, idxs):

                if pos == -1:
                    continue

                chunk_id = self.index.ids[pos]

                chunk = db.query(models.Chunk).join(models.Document).filter(
                    models.Chunk.id == chunk_id,
                    models.Document.user_id == self.user_id
                ).first()

                if not chunk:
                    continue

                if document_ids and chunk.document_id not in document_ids:
                    continue

                candidates.append(chunk)

            if not candidates:
                return []

            # ---------------------------
            # BM25 keyword retrieval
            # ---------------------------

            corpus = [c.content.split() for c in candidates]

            bm25 = BM25Okapi(corpus)

            query_tokens = query.split()

            bm25_scores = bm25.get_scores(query_tokens)

            # ---------------------------
            # Cross-encoder reranking
            # ---------------------------

            pairs = [(query, c.content) for c in candidates]

            rerank_scores = self.reranker.predict(pairs)

            results = []

            for chunk, bm25_score, rerank_score in zip(
                candidates, bm25_scores, rerank_scores
            ):

                text_lower = chunk.content.lower()

                boost = 0
                if keywords:
                    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
                    boost = hits * 0.05

                final_score = float(rerank_score) + (bm25_score * 0.1) + boost

                snippet = make_snippet(chunk.content, query)

                doc_name = chunk.document.filename if chunk.document else "Unknown"

                results.append({
                    "document": doc_name,
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.id,
                    "page": chunk.page,
                    "content": chunk.content,
                    "snippet": snippet,
                    "score": final_score
                })

            results.sort(key=lambda x: x["score"], reverse=True)

            return results[:k]

        finally:
            db.close()

    # --------------------------------------------------
    # Streaming search (for SSE)
    # --------------------------------------------------
    def stream_search(
        self,
        query: str,
        k: int = 5,
        keywords: list[str] | None = None,
        document_ids: list[int] | None = None
    ):

        self.index.load()

        qvec = self.embedder.embed_query(query)

        distances, idxs = self.index.search(qvec, k=50)

        db = SessionLocal()

        try:

            candidates = []

            for score, pos in zip(distances, idxs):

                if pos == -1:
                    continue

                chunk_id = self.index.ids[pos]

                chunk = db.query(models.Chunk).join(models.Document).filter(
                    models.Chunk.id == chunk_id,
                    models.Document.user_id == self.user_id
                ).first()

                if not chunk:
                    continue

                if document_ids and chunk.document_id not in document_ids:
                    continue

                candidates.append(chunk)

            # ---------------------------
            # Stream results progressively
            # ---------------------------
            count = 0
            for chunk in candidates:
                if count >= k:
                    break

                rerank_score = float(
                    self.reranker.predict([(query, chunk.content)])[0]
                )

                text_lower = chunk.content.lower()

                boost = 0
                if keywords:
                    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
                    boost = hits * 0.05

                final_score = rerank_score + boost

                snippet = make_snippet(chunk.content, query)

                doc_name = chunk.document.filename if chunk.document else "Unknown"

                yield {
                    "document": doc_name,
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.id,
                    "page": chunk.page,
                    "content": chunk.content,
                    "snippet": snippet,
                    "score": final_score
                }
                count += 1
        finally:
            db.close()