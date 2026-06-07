"""Qdrant client and collection setup."""
from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import get_settings
from app.services.rag.embedder import embed_dim

COLLECTION_NAME = "medical_docs"
_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    """Lazy Qdrant client."""
    global _client
    if _client is None:
        _client = QdrantClient(url=get_settings().QDRANT_URL)
    return _client


def ensure_collection() -> None:
    """Create medical_docs collection if not exists (dim from embed model)."""
    client = get_client()
    try:
        client.get_collection(COLLECTION_NAME)
    except Exception:
        dim = embed_dim()
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )


def delete_collection() -> None:
    """Delete medical_docs collection. Used before full re-ingest."""
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
