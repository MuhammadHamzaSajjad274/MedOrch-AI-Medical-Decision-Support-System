"""Auth: register, login, me."""
import pytest


def test_register_and_login(client):
    email = "test-pytest@example.com"
    password = "testpass123"
    # Register
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    token = data["access_token"]
    # Me
    r2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    me = r2.json()
    assert me["email"] == email
    assert "id" in me


def test_login_wrong_password(client):
    email = "wrong-pwd@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "right123"})
    r = client.post(
        "/api/auth/login",
        json={"email": email, "password": "wrong"},
    )
    assert r.status_code in (401, 422)


def test_me_unauthorized(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401
    r2 = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
    assert r2.status_code == 401
