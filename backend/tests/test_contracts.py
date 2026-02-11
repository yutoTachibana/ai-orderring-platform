from app.models.company import Company
from app.models.project import Project
from app.models.engineer import Engineer
from app.models.quotation import Quotation
from app.models.order import Order


API = "/api/v1/contracts"


def _prerequisites(db, suffix="1"):
    co = Company(name=f"Test Client {suffix}", company_type="client")
    db.add(co)
    db.flush()
    p = Project(name=f"Test Project {suffix}", client_company_id=co.id)
    db.add(p)
    db.flush()
    e = Engineer(full_name=f"Test Engineer {suffix}", email=f"eng{suffix}@test.com")
    db.add(e)
    db.flush()
    q = Quotation(project_id=p.id, engineer_id=e.id, unit_price=500000, estimated_hours=160, total_amount=500000)
    db.add(q)
    db.flush()
    o = Order(quotation_id=q.id, order_number=f"ORD-{suffix}")
    db.add(o)
    db.commit()
    db.refresh(o)
    db.refresh(p)
    db.refresh(e)
    return o, p, e


def _prerequisites2(db):
    return _prerequisites(db, suffix="2")


def test_list_contracts_unauthenticated(client):
    response = client.get(API)
    assert response.status_code == 401


def test_create_contract(auth_client, db):
    o, p, e = _prerequisites(db)
    response = auth_client.post(API, json={
        "order_id": o.id, "contract_number": "CON-001",
        "contract_type": "quasi_delegation",
        "engineer_id": e.id, "project_id": p.id,
        "start_date": "2026-04-01", "end_date": "2026-09-30",
        "monthly_rate": 800000,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["contract_number"] == "CON-001"
    assert data["monthly_rate"] == 800000


def test_get_contract(auth_client, db):
    o, p, e = _prerequisites(db)
    res = auth_client.post(API, json={
        "order_id": o.id, "contract_number": "CON-002",
        "contract_type": "quasi_delegation",
        "engineer_id": e.id, "project_id": p.id,
        "start_date": "2026-04-01", "end_date": "2026-09-30",
        "monthly_rate": 750000,
    })
    cid = res.json()["id"]
    response = auth_client.get(f"{API}/{cid}")
    assert response.status_code == 200
    assert response.json()["monthly_rate"] == 750000


def test_get_contract_not_found(auth_client):
    assert auth_client.get(f"{API}/99999").status_code == 404


def test_update_contract(auth_client, db):
    o, p, e = _prerequisites(db)
    res = auth_client.post(API, json={
        "order_id": o.id, "contract_number": "CON-003",
        "contract_type": "quasi_delegation",
        "engineer_id": e.id, "project_id": p.id,
        "start_date": "2026-04-01", "end_date": "2026-09-30",
        "monthly_rate": 700000,
    })
    cid = res.json()["id"]
    response = auth_client.put(f"{API}/{cid}", json={"monthly_rate": 900000})
    assert response.status_code == 200
    assert response.json()["monthly_rate"] == 900000


def test_delete_contract(auth_client, db):
    o, p, e = _prerequisites(db)
    res = auth_client.post(API, json={
        "order_id": o.id, "contract_number": "CON-004",
        "contract_type": "quasi_delegation",
        "engineer_id": e.id, "project_id": p.id,
        "start_date": "2026-04-01", "end_date": "2026-09-30",
        "monthly_rate": 650000,
    })
    cid = res.json()["id"]
    assert auth_client.delete(f"{API}/{cid}").status_code == 204
    assert auth_client.get(f"{API}/{cid}").status_code == 404


def test_list_contracts_with_filter(auth_client, db):
    o, p, e = _prerequisites(db)
    auth_client.post(API, json={
        "order_id": o.id, "contract_number": "CON-005",
        "contract_type": "quasi_delegation",
        "engineer_id": e.id, "project_id": p.id,
        "start_date": "2026-04-01", "end_date": "2026-09-30",
        "monthly_rate": 600000, "status": "draft",
    })
    o2, p2, e2 = _prerequisites2(db)
    auth_client.post(API, json={
        "order_id": o2.id, "contract_number": "CON-006",
        "contract_type": "quasi_delegation",
        "engineer_id": e2.id, "project_id": p2.id,
        "start_date": "2026-04-01", "end_date": "2026-09-30",
        "monthly_rate": 550000, "status": "active",
    })
    res = auth_client.get(f"{API}?status=draft")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert all(c["status"] == "draft" for c in data["items"])
