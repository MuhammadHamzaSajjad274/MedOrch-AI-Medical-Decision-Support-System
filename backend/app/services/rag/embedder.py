"""Lightweight embedder: all-MiniLM-L6-v2. Respects EMBED_DEVICE (cpu/cuda/auto)."""
from __future__ import annotations

from app.core.config import get_settings

_settings = get_settings()
_embedder = None


def _device() -> str:
    d = _settings.EMBED_DEVICE
    if d == "auto":
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"
    return d


def get_embedder():
    """Lazy-load sentence-transformers model."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            device=_device(),
        )
    return _embedder


def embed(texts: list[str]) -> list[list[float]]:
    """Return list of vectors for given texts."""
    model = get_embedder()
    return model.encode(texts, convert_to_numpy=True).tolist()


def embed_dim() -> int:
    """Dimension of embedding vectors."""
    model = get_embedder()
    return model.get_sentence_embedding_dimension()
