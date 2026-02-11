"""Tests for /api/v1/auth endpoints."""


def test_signup(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "new@example.com",
            "password": "securepassword",
            "full_name": "New User",
            "role": "sales",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["full_name"] == "New User"
    assert data["role"] == "sales"
    assert data["is_active"] is True
    assert "id" in data


def test_signup_duplicate_email(client):
    payload = {
        "email": "dup@example.com",
        "password": "pass1234",
        "full_name": "First",
        "role": "sales",
    }
    client.post("/api/v1/auth/signup", json=payload)
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 400


def test_login(client):
    # Create a user first
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "login@example.com",
            "password": "mypassword",
            "full_name": "Login User",
            "role": "sales",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "login@example.com", "password": "mypassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "wrong@example.com",
            "password": "correct",
            "full_name": "Wrong Pass",
            "role": "sales",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "wrong@example.com", "password": "incorrect"},
    )
    assert response.status_code == 401


def test_me_without_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_token(auth_client):
    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
