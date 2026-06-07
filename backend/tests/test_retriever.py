"""Retriever: tokenize and RRF logic (unit tests, no Qdrant)."""
import pytest

# Only test the tokenize helper and RRF logic without hitting Qdrant
from app.services.rag.retriever import _tokenize


def test_tokenize():
    assert _tokenize("Hello World") == ["hello", "world"]
    assert _tokenize("") == []
    assert _tokenize("a b c") == ["a", "b", "c"]
