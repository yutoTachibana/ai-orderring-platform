from app.models.company import Company
from app.models.project import Project, SubcontractingTierLimit
from app.models.engineer import Engineer, EmploymentType


API = "/api/v1/quotations"


def _setup(db, tier_limit=None, employment_type=EmploymentType.proper, with_company=False):
    co = Company(name="Test Client", company_type="client")
    db.add(co)
    db.flush()
    p = Project(name="Test Project", client_company_id=co.id, subcontracting_tier_limit=tier_limit)
    db.add(p)
    db.flush()
    company_id = None
    if with_company:
        ses_co = Company(name="SES Co", company_type="ses")
        db.add(ses_co)
        db.flush()
        company_id = ses_co.id
    e = Engineer(
        full_name="Test Engineer",
        email="eng@test.com",
        employment_type=employment_type,
        company_id=company_id,
    )
    db.add(e)
    db.commit()
    db.refresh(p)
    db.refresh(e)
    return p, e


def test_list_quotations_unauthenticated(client):
    response = client.get(API)
    assert response.status_code == 401


def test_create_quotation(auth_client, db):
    p, e = _setup(db)
    response = auth_client.post(API, json={
        "project_id": p.id, "engineer_id": e.id,
        "unit_price": 100, "estimated_hours": 40, "total_amount": 4000,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["unit_price"] == 100
    assert data["status"] == "draft"
    assert "id" in data


def test_get_quotation(auth_client, db):
    p, e = _setup(db)
    res = auth_client.post(API, json={
        "project_id": p.id, "engineer_id": e.id,
        "unit_price": 150, "estimated_hours": 30, "total_amount": 4500,
    })
    qid = res.json()["id"]
    response = auth_client.get(f"{API}/{qid}")
    assert response.status_code == 200
    assert response.json()["unit_price"] == 150


def test_get_quotation_not_found(auth_client):
    assert auth_client.get(f"{API}/9999").status_code == 404


def test_update_quotation(auth_client, db):
    p, e = _setup(db)
    res = auth_client.post(API, json={
        "project_id": p.id, "engineer_id": e.id,
        "unit_price": 100, "estimated_hours": 40, "total_amount": 4000,
    })
    qid = res.json()["id"]
    response = auth_client.put(f"{API}/{qid}", json={"unit_price": 120, "total_amount": 4800})
    assert response.status_code == 200
    assert response.json()["unit_price"] == 120


def test_delete_quotation(auth_client, db):
    p, e = _setup(db)
    res = auth_client.post(API, json={
        "project_id": p.id, "engineer_id": e.id,
        "unit_price": 100, "estimated_hours": 40, "total_amount": 4000,
    })
    qid = res.json()["id"]
    assert auth_client.delete(f"{API}/{qid}").status_code == 204
    assert auth_client.get(f"{API}/{qid}").status_code == 404


def test_submit_quotation(auth_client, db):
    p, e = _setup(db)
    res = auth_client.post(API, json={
        "project_id": p.id, "engineer_id": e.id,
        "unit_price": 100, "estimated_hours": 40, "total_amount": 4000,
    })
    qid = res.json()["id"]
    response = auth_client.post(f"{API}/{qid}/submit")
    assert response.status_code == 200
    assert response.json()["status"] == "submitted"


def test_submit_quotation_wrong_status(auth_client, db):
    p, e = _setup(db)
    res = auth_client.post(API, json={
        "project_id": p.id, "engineer_id": e.id,
        "unit_price": 100, "estimated_hours": 40, "total_amount": 4000,
    })
    qid = res.json()["id"]
    auth_client.post(f"{API}/{qid}/submit")  # now submitted
    response = auth_client.post(f"{API}/{qid}/submit")
    assert response.status_code == 400


def test_approve_quotation(auth_client, db):
    p, e = _setup(db)
    res = auth_client.post(API, json={
        "project_id": p.id, "engineer_id": e.id,
        "unit_price": 100, "estimated_hours": 40, "total_amount": 4000,
    })
    qid = res.json()["id"]
    auth_client.post(f"{API}/{qid}/submit")
    response = auth_client.post(f"{API}/{qid}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_approve_quotation_wrong_status(auth_client, db):
    p, e = _setup(db)
    res = auth_client.post(API, json={
        "project_id": p.id, "engineer_id": e.id,
        "unit_price": 100, "estimated_hours": 40, "total_amount": 4000,
    })
    qid = res.json()["id"]
    response = auth_client.post(f"{API}/{qid}/approve")  # still draft
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# 商流制約 (Subcontracting tier constraint) tests
# ---------------------------------------------------------------------------


def test_create_quotation_tier_eligible(auth_client, db):
    """プロパーのみ制限 + プロパーエンジニア → 201 成功"""
    p, e = _setup(db, tier_limit=SubcontractingTierLimit.proper_only, employment_type=EmploymentType.proper)
    response = auth_client.post(API, json={
        "project_id": p.id, "engineer_id": e.id,
        "unit_price": 100, "estimated_hours": 40, "total_amount": 4000,
    })
    assert response.status_code == 201


def test_create_quotation_tier_violation(auth_client, db):
    """プロパーのみ制限 + フリーランスエンジニア → 400 エラー"""
    p, e = _setup(db, tier_limit=SubcontractingTierLimit.proper_only, employment_type=EmploymentType.freelancer)
    response = auth_client.post(API, json={
        "project_id": p.id, "engineer_id": e.id,
        "unit_price": 100, "estimated_hours": 40, "total_amount": 4000,
    })
    assert response.status_code == 400
    assert "商流制約違反" in response.json()["detail"]


def test_create_quotation_first_tier_freelancer_ok(auth_client, db):
    """一社先まで制限 + 直接契約フリーランス → 201 成功"""
    p, e = _setup(db, tier_limit=SubcontractingTierLimit.first_tier, employment_type=EmploymentType.freelancer)
    response = auth_client.post(API, json={
        "project_id": p.id, "engineer_id": e.id,
        "unit_price": 100, "estimated_hours": 40, "total_amount": 4000,
    })
    assert response.status_code == 201


def test_create_quotation_first_tier_partner_violation(auth_client, db):
    """一社先まで制限 + パートナー経由フリーランス → 400 エラー"""
    p, e = _setup(
        db,
        tier_limit=SubcontractingTierLimit.first_tier,
        employment_type=EmploymentType.freelancer,
        with_company=True,
    )
    response = auth_client.post(API, json={
        "project_id": p.id, "engineer_id": e.id,
        "unit_price": 100, "estimated_hours": 40, "total_amount": 4000,
    })
    assert response.status_code == 400
    assert "商流制約違反" in response.json()["detail"]


def test_create_quotation_no_restriction(auth_client, db):
    """制限なし + パートナー経由フリーランス → 201 成功"""
    p, e = _setup(
        db,
        tier_limit=SubcontractingTierLimit.no_restriction,
        employment_type=EmploymentType.freelancer,
        with_company=True,
    )
    response = auth_client.post(API, json={
        "project_id": p.id, "engineer_id": e.id,
        "unit_price": 100, "estimated_hours": 40, "total_amount": 4000,
    })
    assert response.status_code == 201
