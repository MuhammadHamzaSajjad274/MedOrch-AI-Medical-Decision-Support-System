"""Consultations: list and get (require auth)."""
import pytest


@pytest.fixture
def auth_headers(client):
    """Register, login, return Authorization header."""
    r = client.post(
        "/api/auth/register",
        json={"email": "consult-test@example.com", "password": "pass123"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_consultations_list_unauthorized(client):
    r = client.get("/api/consultations")
    assert r.status_code == 401


def test_consultations_list_empty(client, auth_headers):
    r = client.get("/api/consultations", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_consultations_get_404(client, auth_headers):
    r = client.get(
        "/api/consultations/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert r.status_code == 404
