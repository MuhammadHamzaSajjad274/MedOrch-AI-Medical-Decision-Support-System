"""Health and RAG status endpoints."""
import pytest


def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("ok", "degraded")
    assert "qdrant_reachable" in data
    assert "cuda_available" in data
    assert "device" in data


def test_rag_status(client):
    r = client.get("/api/rag/status")
    assert r.status_code == 200
    data = r.json()
    assert data["collection"] == "medical_docs"
    assert "points_count" in data
    assert "ready" in data


def test_reset(client):
    r = client.post("/api/reset")
    assert r.status_code == 204
