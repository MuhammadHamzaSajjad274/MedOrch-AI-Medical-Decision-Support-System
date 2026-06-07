"""Pytest fixtures. Set test DB before any app import."""
import os
import sys

# Use in-memory SQLite for tests (set before app imports)
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("LLM_BASE_URL", "http://localhost:11434/v1")
os.environ.setdefault("LLM_MODEL", "mistral-7b-medical")

# Ensure backend is on path
_backend = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _backend not in sys.path:
    sys.path.insert(0, _backend)

import pytest
from fastapi.testclient import TestClient

# Import after env is set
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)
