"""Retrieve top-k chunks: dense search + keyword re-rank (RRF-style)."""
from __future__ import annotations

from rank_bm25 import BM25Okapi

from app.services.rag.embedder import embed
from app.services.rag.qdrant_client import COLLECTION_NAME, ensure_collection, get_client

# Fetch more from dense search, then re-rank with BM25 and take top k
DENSE_LIMIT = 20
RRF_K = 60


def _tokenize(text: str) -> list[str]:
    """Simple tokenization for BM25."""
    return text.lower().split()


def retrieve(query: str, k: int = 5) -> list[dict]:
    """
    Dense search then keyword re-rank. Return list of dicts with keys:
    text, source, page (optional), score.
    """
    try:
        ensure_collection()
        client = get_client()
        [vec] = embed([query])
        hits = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vec,
            limit=DENSE_LIMIT,
        )
        if not hits:
            return []
        docs = [
            {
                "text": h.payload.get("text", ""),
                "source": h.payload.get("source", ""),
                "page": h.payload.get("page"),
                "score": h.score,
            }
            for h in hits
        ]
        # Re-rank by BM25 keyword overlap
        corpus = [_tokenize(d["text"]) for d in docs]
        bm25 = BM25Okapi(corpus)
        query_tokens = _tokenize(query)
        bm25_scores = bm25.get_scores(query_tokens)
        # RRF: 1 / (k + rank). Dense order = hit order (0=best); BM25 rank by score.
        bm25_rank_order = sorted(
            range(len(bm25_scores)), key=lambda i: -bm25_scores[i]
        )
        bm25_ranks = {idx: r for r, idx in enumerate(bm25_rank_order)}
        rrf_scores = []
        for i in range(len(docs)):
            dense_rank = i
            bm25_rank = bm25_ranks.get(i, RRF_K)
            rrf = 1 / (RRF_K + dense_rank) + 1 / (RRF_K + bm25_rank)
            rrf_scores.append((rrf, i))
        rrf_scores.sort(key=lambda x: -x[0])
        top_indices = [i for _, i in rrf_scores[:k]]
        return [docs[i] for i in top_indices]
    except Exception:
        return []
