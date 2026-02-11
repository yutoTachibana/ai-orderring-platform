from app.models.company import Company
from app.models.project import Project
from app.models.engineer import Engineer
from app.models.quotation import Quotation


API = "/api/v1/orders"


def _create_quotation(db):
    co = Company(name="Test Client", company_type="client")
    db.add(co)
    db.flush()
    p = Project(name="Test Project", client_company_id=co.id)
    db.add(p)
    db.flush()
    e = Engineer(full_name="Test Engineer", email="eng@test.com")
    db.add(e)
    db.flush()
    q = Quotation(project_id=p.id, engineer_id=e.id, unit_price=500000, estimated_hours=160, total_amount=500000)
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


def test_list_orders_unauthenticated(client):
    response = client.get(API)
    assert response.status_code == 401


def test_create_order(auth_client, db):
    q = _create_quotation(db)
    response = auth_client.post(API, json={
        "quotation_id": q.id, "order_number": "ORD-001",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["order_number"] == "ORD-001"
    assert data["status"] == "pending"


def test_get_order(auth_client, db):
    q = _create_quotation(db)
    res = auth_client.post(API, json={"quotation_id": q.id, "order_number": "ORD-002"})
    oid = res.json()["id"]
    response = auth_client.get(f"{API}/{oid}")
    assert response.status_code == 200
    assert response.json()["order_number"] == "ORD-002"


def test_get_order_not_found(auth_client):
    assert auth_client.get(f"{API}/99999").status_code == 404


def test_update_order(auth_client, db):
    q = _create_quotation(db)
    res = auth_client.post(API, json={"quotation_id": q.id, "order_number": "ORD-003"})
    oid = res.json()["id"]
    response = auth_client.put(f"{API}/{oid}", json={"notes": "Updated"})
    assert response.status_code == 200
    assert response.json()["notes"] == "Updated"


def test_delete_order(auth_client, db):
    q = _create_quotation(db)
    res = auth_client.post(API, json={"quotation_id": q.id, "order_number": "ORD-004"})
    oid = res.json()["id"]
    assert auth_client.delete(f"{API}/{oid}").status_code == 204
    assert auth_client.get(f"{API}/{oid}").status_code == 404


def test_confirm_order(auth_client, db):
    q = _create_quotation(db)
    res = auth_client.post(API, json={"quotation_id": q.id, "order_number": "ORD-005"})
    oid = res.json()["id"]
    response = auth_client.post(f"{API}/{oid}/confirm")
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


def test_confirm_order_wrong_status(auth_client, db):
    q = _create_quotation(db)
    res = auth_client.post(API, json={"quotation_id": q.id, "order_number": "ORD-006"})
    oid = res.json()["id"]
    auth_client.post(f"{API}/{oid}/confirm")  # now confirmed
    response = auth_client.post(f"{API}/{oid}/confirm")
    assert response.status_code == 400
