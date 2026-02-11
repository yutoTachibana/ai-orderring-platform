from app.models.company import Company


API = "/api/v1/projects"


def _create_company(db):
    c = Company(name="Test Client", company_type="client")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def test_list_projects_unauthenticated(client):
    response = client.get(API)
    assert response.status_code == 401


def test_list_projects_empty(auth_client):
    response = auth_client.get(API)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_create_project(auth_client, db):
    company = _create_company(db)
    response = auth_client.post(API, json={
        "name": "Test Project",
        "client_company_id": company.id,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["status"] == "draft"
    assert "id" in data


def test_get_project(auth_client, db):
    company = _create_company(db)
    res = auth_client.post(API, json={"name": "P1", "client_company_id": company.id})
    pid = res.json()["id"]
    response = auth_client.get(f"{API}/{pid}")
    assert response.status_code == 200
    assert response.json()["name"] == "P1"


def test_get_project_not_found(auth_client):
    response = auth_client.get(f"{API}/99999")
    assert response.status_code == 404


def test_update_project(auth_client, db):
    company = _create_company(db)
    res = auth_client.post(API, json={"name": "Original", "client_company_id": company.id})
    pid = res.json()["id"]
    response = auth_client.put(f"{API}/{pid}", json={"name": "Updated"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"


def test_delete_project(auth_client, db):
    company = _create_company(db)
    res = auth_client.post(API, json={"name": "ToDelete", "client_company_id": company.id})
    pid = res.json()["id"]
    assert auth_client.delete(f"{API}/{pid}").status_code == 204
    assert auth_client.get(f"{API}/{pid}").status_code == 404


def test_list_projects_with_filter(auth_client, db):
    company = _create_company(db)
    auth_client.post(API, json={"name": "Draft", "client_company_id": company.id, "status": "draft"})
    auth_client.post(API, json={"name": "Open", "client_company_id": company.id, "status": "open"})
    res = auth_client.get(f"{API}?status=draft")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Draft"
