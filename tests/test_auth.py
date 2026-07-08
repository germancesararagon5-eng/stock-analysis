import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def registered_user():
    resp = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 201
    return resp.json()["access_token"]


def test_register():
    resp = client.post("/api/auth/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data


def test_register_duplicate_username():
    client.post("/api/auth/register", json={
        "username": "dupuser",
        "email": "dup1@example.com",
        "password": "secret123",
    })
    resp = client.post("/api/auth/register", json={
        "username": "dupuser",
        "email": "dup2@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 400


def test_register_duplicate_email():
    client.post("/api/auth/register", json={
        "username": "user1",
        "email": "dup@example.com",
        "password": "secret123",
    })
    resp = client.post("/api/auth/register", json={
        "username": "user2",
        "email": "dup@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 400


def test_login(registered_user):
    resp = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "secret123",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password():
    client.post("/api/auth/register", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "correct",
    })
    resp = client.post("/api/auth/login", json={
        "username": "loginuser",
        "password": "wrong",
    })
    assert resp.status_code == 401


def test_me(registered_user):
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {registered_user}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testuser"


def test_me_no_token():
    resp = client.get("/api/auth/me")
    assert resp.status_code in (401, 403)


def test_me_invalid_token():
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401
