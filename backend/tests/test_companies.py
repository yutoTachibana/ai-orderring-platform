"""Tests for /api/v1/companies CRUD endpoints."""


def _make_company(**overrides):
    defaults = {
        "name": "Test Corp",
        "company_type": "client",
        "address": "Tokyo, Japan",
        "phone": "03-1234-5678",
        "email": "info@testcorp.jp",
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_companies_unauthenticated(client):
    response = client.get("/api/v1/companies")
    assert response.status_code == 401


def test_list_companies_empty(auth_client):
    response = auth_client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_company(auth_client):
    response = auth_client.post("/api/v1/companies", json=_make_company())
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Corp"
    assert data["company_type"] == "client"
    assert "id" in data


# ---------------------------------------------------------------------------
# Get single
# ---------------------------------------------------------------------------


def test_get_company(auth_client):
    created = auth_client.post("/api/v1/companies", json=_make_company()).json()
    response = auth_client.get(f"/api/v1/companies/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Corp"


def test_get_company_not_found(auth_client):
    response = auth_client.get("/api/v1/companies/99999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_company(auth_client):
    created = auth_client.post("/api/v1/companies", json=_make_company()).json()
    response = auth_client.put(
        f"/api/v1/companies/{created['id']}",
        json={"name": "Updated Corp"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Corp"


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_company(auth_client):
    created = auth_client.post("/api/v1/companies", json=_make_company()).json()
    response = auth_client.delete(f"/api/v1/companies/{created['id']}")
    assert response.status_code == 204

    # Verify deleted
    response = auth_client.get(f"/api/v1/companies/{created['id']}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# List with data
# ---------------------------------------------------------------------------


def test_list_companies_with_data(auth_client):
    auth_client.post("/api/v1/companies", json=_make_company(name="Alpha"))
    auth_client.post("/api/v1/companies", json=_make_company(name="Beta"))
    response = auth_client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
