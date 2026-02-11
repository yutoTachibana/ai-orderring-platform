"""Tests for /api/v1/engineers CRUD endpoints."""

from app.models.company import Company
from app.models.project import Project, SubcontractingTierLimit
from app.models.engineer import Engineer, EmploymentType


def _make_engineer(**overrides):
    defaults = {
        "full_name": "John Doe",
        "email": "john@example.com",
        "phone": "09012345678",
        "hourly_rate": 5000,
        "monthly_rate": 700000,
        "employment_type": "proper",
        "availability_status": "available",
        "years_of_experience": 5,
        "notes": "Senior Python developer",
        "is_active": True,
        "skill_ids": [],
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_engineers_unauthenticated(client):
    response = client.get("/api/v1/engineers")
    assert response.status_code == 401


def test_list_engineers_empty(auth_client):
    response = auth_client.get("/api/v1/engineers")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_engineer(auth_client):
    response = auth_client.post("/api/v1/engineers", json=_make_engineer())
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["availability_status"] == "available"
    assert "id" in data


# ---------------------------------------------------------------------------
# Get single
# ---------------------------------------------------------------------------


def test_get_engineer(auth_client):
    created = auth_client.post("/api/v1/engineers", json=_make_engineer()).json()
    response = auth_client.get(f"/api/v1/engineers/{created['id']}")
    assert response.status_code == 200
    assert response.json()["full_name"] == "John Doe"


def test_get_engineer_not_found(auth_client):
    response = auth_client.get("/api/v1/engineers/99999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_engineer(auth_client):
    created = auth_client.post("/api/v1/engineers", json=_make_engineer()).json()
    response = auth_client.put(
        f"/api/v1/engineers/{created['id']}",
        json={"full_name": "Jane Doe"},
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Jane Doe"


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_engineer(auth_client):
    created = auth_client.post("/api/v1/engineers", json=_make_engineer()).json()
    response = auth_client.delete(f"/api/v1/engineers/{created['id']}")
    assert response.status_code == 204

    # Verify deleted
    response = auth_client.get(f"/api/v1/engineers/{created['id']}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# List with data
# ---------------------------------------------------------------------------


def test_list_engineers_with_data(auth_client):
    auth_client.post("/api/v1/engineers", json=_make_engineer(full_name="Alice"))
    auth_client.post("/api/v1/engineers", json=_make_engineer(full_name="Bob"))
    response = auth_client.get("/api/v1/engineers")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


# ---------------------------------------------------------------------------
# Employment type & subcontracting tier
# ---------------------------------------------------------------------------


def test_create_engineer_with_employment_type(auth_client):
    response = auth_client.post("/api/v1/engineers", json=_make_engineer(employment_type="freelancer"))
    assert response.status_code == 201
    data = response.json()
    assert data["employment_type"] == "freelancer"
    assert data["subcontracting_tier"] == 1  # freelancer without company → tier 1


def test_create_engineer_default_employment_type(auth_client):
    response = auth_client.post("/api/v1/engineers", json=_make_engineer())
    assert response.status_code == 201
    data = response.json()
    assert data["employment_type"] == "proper"
    assert data["subcontracting_tier"] == 0  # proper → tier 0


def test_engineer_response_includes_tier(auth_client):
    created = auth_client.post("/api/v1/engineers", json=_make_engineer()).json()
    response = auth_client.get(f"/api/v1/engineers/{created['id']}")
    assert response.status_code == 200
    assert "subcontracting_tier" in response.json()


# ---------------------------------------------------------------------------
# /eligible endpoint
# ---------------------------------------------------------------------------


def test_eligible_endpoint_filters_by_tier(auth_client, db):
    """適格エンドポイントが再委託制限に基づきフィルタリングする"""
    co = Company(name="Client", company_type="client")
    db.add(co)
    db.flush()
    ses_co = Company(name="SES Co", company_type="ses")
    db.add(ses_co)
    db.flush()
    p = Project(
        name="Proper Only Project",
        client_company_id=co.id,
        subcontracting_tier_limit=SubcontractingTierLimit.proper_only,
    )
    db.add(p)
    db.flush()
    # プロパーエンジニア（適格）
    e1 = Engineer(full_name="Proper Eng", email="p@t.com", employment_type=EmploymentType.proper, is_active=True)
    db.add(e1)
    db.flush()
    # フリーランスエンジニア（不適格）
    e2 = Engineer(full_name="FL Eng", email="fl@t.com", employment_type=EmploymentType.freelancer, is_active=True)
    db.add(e2)
    db.flush()
    # パートナー経由フリーランス（不適格）
    e3 = Engineer(
        full_name="Partner Eng", email="partner@t.com",
        employment_type=EmploymentType.freelancer,
        company_id=ses_co.id, is_active=True,
    )
    db.add(e3)
    db.commit()
    db.refresh(p)

    response = auth_client.get(f"/api/v1/engineers/eligible?project_id={p.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["full_name"] == "Proper Eng"


def test_eligible_endpoint_no_restriction(auth_client, db):
    """制限なしの場合は全エンジニアが返される"""
    co = Company(name="Client", company_type="client")
    db.add(co)
    db.flush()
    p = Project(name="No Limit Project", client_company_id=co.id, subcontracting_tier_limit=None)
    db.add(p)
    db.flush()
    e1 = Engineer(full_name="Eng1", email="e1@t.com", employment_type=EmploymentType.proper, is_active=True)
    e2 = Engineer(full_name="Eng2", email="e2@t.com", employment_type=EmploymentType.freelancer, is_active=True)
    db.add_all([e1, e2])
    db.commit()
    db.refresh(p)

    response = auth_client.get(f"/api/v1/engineers/eligible?project_id={p.id}")
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_eligible_endpoint_project_not_found(auth_client):
    response = auth_client.get("/api/v1/engineers/eligible?project_id=99999")
    assert response.status_code == 404
