from app.models.company import Company
from app.models.project import Project
from app.models.engineer import Engineer
from app.models.quotation import Quotation
from app.models.order import Order


API = "/api/v1/invoices"


def _create_contract_via_api(auth_client, db):
    """Create full chain via API and return contract_id."""
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
    db.flush()
    o = Order(quotation_id=q.id, order_number="ORD-001")
    db.add(o)
    db.commit()
    db.refresh(o)
    db.refresh(p)
    db.refresh(e)

    res = auth_client.post("/api/v1/contracts", json={
        "order_id": o.id, "contract_number": "CON-001",
        "contract_type": "quasi_delegation",
        "engineer_id": e.id, "project_id": p.id,
        "start_date": "2026-04-01", "end_date": "2026-09-30",
        "monthly_rate": 500000,
    })
    assert res.status_code == 201
    return res.json()["id"]


def _invoice_data(contract_id, num="001"):
    return {
        "contract_id": contract_id,
        "invoice_number": f"INV-{num}",
        "billing_month": "2026-04-01",
        "working_hours": 160.0,
        "base_amount": 500000,
        "adjustment_amount": 0,
        "tax_amount": 50000,
        "total_amount": 550000,
    }


def test_list_invoices_unauthenticated(client):
    assert client.get(API).status_code == 401


def test_create_invoice(auth_client, db):
    cid = _create_contract_via_api(auth_client, db)
    response = auth_client.post(API, json=_invoice_data(cid))
    assert response.status_code == 201
    data = response.json()
    assert data["invoice_number"] == "INV-001"
    assert data["status"] == "draft"
    assert data["total_amount"] == 550000


def test_get_invoice(auth_client, db):
    cid = _create_contract_via_api(auth_client, db)
    res = auth_client.post(API, json=_invoice_data(cid))
    iid = res.json()["id"]
    response = auth_client.get(f"{API}/{iid}")
    assert response.status_code == 200
    assert response.json()["invoice_number"] == "INV-001"


def test_get_invoice_not_found(auth_client):
    assert auth_client.get(f"{API}/99999").status_code == 404


def test_update_invoice(auth_client, db):
    cid = _create_contract_via_api(auth_client, db)
    res = auth_client.post(API, json=_invoice_data(cid))
    iid = res.json()["id"]
    response = auth_client.put(f"{API}/{iid}", json={"working_hours": 165.0})
    assert response.status_code == 200
    assert response.json()["working_hours"] == 165.0


def test_delete_invoice(auth_client, db):
    cid = _create_contract_via_api(auth_client, db)
    res = auth_client.post(API, json=_invoice_data(cid))
    iid = res.json()["id"]
    assert auth_client.delete(f"{API}/{iid}").status_code == 204
    assert auth_client.get(f"{API}/{iid}").status_code == 404


def test_send_invoice(auth_client, db):
    cid = _create_contract_via_api(auth_client, db)
    res = auth_client.post(API, json=_invoice_data(cid))
    iid = res.json()["id"]
    response = auth_client.post(f"{API}/{iid}/send")
    assert response.status_code == 200
    assert response.json()["status"] == "sent"


def test_send_invoice_wrong_status(auth_client, db):
    cid = _create_contract_via_api(auth_client, db)
    res = auth_client.post(API, json=_invoice_data(cid))
    iid = res.json()["id"]
    auth_client.post(f"{API}/{iid}/send")  # now sent
    response = auth_client.post(f"{API}/{iid}/send")
    assert response.status_code == 400


def test_pay_invoice(auth_client, db):
    cid = _create_contract_via_api(auth_client, db)
    res = auth_client.post(API, json=_invoice_data(cid))
    iid = res.json()["id"]
    auth_client.post(f"{API}/{iid}/send")
    response = auth_client.post(f"{API}/{iid}/pay")
    assert response.status_code == 200
    assert response.json()["status"] == "paid"


def test_pay_invoice_wrong_status(auth_client, db):
    cid = _create_contract_via_api(auth_client, db)
    res = auth_client.post(API, json=_invoice_data(cid))
    iid = res.json()["id"]
    response = auth_client.post(f"{API}/{iid}/pay")  # still draft
    assert response.status_code == 400


def test_invoice_full_lifecycle(auth_client, db):
    cid = _create_contract_via_api(auth_client, db)
    res = auth_client.post(API, json=_invoice_data(cid))
    assert res.status_code == 201
    iid = res.json()["id"]

    send = auth_client.post(f"{API}/{iid}/send")
    assert send.json()["status"] == "sent"

    pay = auth_client.post(f"{API}/{iid}/pay")
    assert pay.json()["status"] == "paid"
