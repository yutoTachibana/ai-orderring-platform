"""ロールベースアクセス制御のテスト。

admin: 全操作可能
sales: 読み取り・作成・更新可能。削除は不可
engineer: 読み取り・作成・更新可能。削除は不可
"""
from app.models.company import Company


API_COMPANIES = "/api/v1/companies"
API_ENGINEERS = "/api/v1/engineers"
API_REPORTS = "/api/v1/reports"


def _create_company(db):
    co = Company(name="Test Corp", company_type="client")
    db.add(co)
    db.commit()
    db.refresh(co)
    return co


# --- Admin can delete ---


def test_admin_can_delete_company(auth_client, db):
    co = _create_company(db)
    response = auth_client.delete(f"{API_COMPANIES}/{co.id}")
    assert response.status_code == 204


def test_admin_can_delete_engineer(auth_client):
    res = auth_client.post(API_ENGINEERS, json={
        "full_name": "Admin Delete Test",
        "email": "admin-del@test.com",
    })
    eid = res.json()["id"]
    response = auth_client.delete(f"{API_ENGINEERS}/{eid}")
    assert response.status_code == 204


# --- Sales cannot delete ---


def test_sales_can_read_companies(sales_client, db):
    _create_company(db)
    response = sales_client.get(API_COMPANIES)
    assert response.status_code == 200
    assert response.json()["total"] >= 1


def test_sales_can_create_company(sales_client):
    response = sales_client.post(API_COMPANIES, json={
        "name": "Sales Created Corp",
        "company_type": "client",
    })
    assert response.status_code == 201


def test_sales_cannot_delete_company(sales_client, db):
    co = _create_company(db)
    response = sales_client.delete(f"{API_COMPANIES}/{co.id}")
    assert response.status_code == 403


def test_sales_cannot_delete_engineer(sales_client):
    res = sales_client.post(API_ENGINEERS, json={
        "full_name": "Sales Test Engineer",
        "email": "sales-eng@test.com",
    })
    eid = res.json()["id"]
    response = sales_client.delete(f"{API_ENGINEERS}/{eid}")
    assert response.status_code == 403


# --- Engineer cannot delete ---


def test_engineer_can_read_companies(engineer_client, db):
    _create_company(db)
    response = engineer_client.get(API_COMPANIES)
    assert response.status_code == 200


def test_engineer_cannot_delete_company(engineer_client, db):
    co = _create_company(db)
    response = engineer_client.delete(f"{API_COMPANIES}/{co.id}")
    assert response.status_code == 403


# --- Report schedule delete requires admin ---


def test_sales_cannot_delete_report_schedule(sales_client):
    res = sales_client.post(f"{API_REPORTS}/schedules", json={
        "name": "Test Schedule",
        "report_type": "monthly_summary",
        "cron_expression": "0 9 1 * *",
    })
    sid = res.json()["id"]
    response = sales_client.delete(f"{API_REPORTS}/schedules/{sid}")
    assert response.status_code == 403


def test_admin_can_delete_report_schedule(auth_client):
    res = auth_client.post(f"{API_REPORTS}/schedules", json={
        "name": "Admin Schedule",
        "report_type": "monthly_summary",
        "cron_expression": "0 9 1 * *",
    })
    sid = res.json()["id"]
    response = auth_client.delete(f"{API_REPORTS}/schedules/{sid}")
    assert response.status_code == 204


# --- Forbidden response has detail ---


def test_forbidden_response_has_detail(sales_client, db):
    co = _create_company(db)
    response = sales_client.delete(f"{API_COMPANIES}/{co.id}")
    assert response.status_code == 403
    assert "ロール" in response.json()["detail"]
