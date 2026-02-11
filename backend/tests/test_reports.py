API = "/api/v1/reports"


def test_report_types_unauthenticated(client):
    response = client.get(f"{API}/types")
    assert response.status_code == 401


def test_report_types(auth_client):
    response = auth_client.get(f"{API}/types")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["type"] == "monthly_summary"


def test_generate_report(auth_client):
    response = auth_client.post(f"{API}/generate", json={
        "report_type": "monthly_summary",
        "year": 2026,
        "month": 1,
    })
    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]
    assert len(response.content) > 0


def test_generate_report_invalid_type(auth_client):
    response = auth_client.post(f"{API}/generate", json={
        "report_type": "invalid_type",
        "year": 2026,
        "month": 1,
    })
    assert response.status_code == 400


def test_list_schedules_empty(auth_client):
    response = auth_client.get(f"{API}/schedules")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_create_schedule(auth_client):
    response = auth_client.post(f"{API}/schedules", json={
        "name": "月次レポート",
        "report_type": "monthly_summary",
        "cron_expression": "0 9 1 * *",
        "recipients": ["admin@test.com"],
        "output_format": "excel",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "月次レポート"
    assert data["cron_expression"] == "0 9 1 * *"
    assert data["is_active"] is True


def test_update_schedule(auth_client):
    res = auth_client.post(f"{API}/schedules", json={
        "name": "Test Schedule",
        "report_type": "monthly_summary",
        "cron_expression": "0 9 1 * *",
    })
    sid = res.json()["id"]
    response = auth_client.put(f"{API}/schedules/{sid}", json={
        "name": "Updated Schedule",
        "is_active": False,
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Schedule"
    assert response.json()["is_active"] is False


def test_delete_schedule(auth_client):
    res = auth_client.post(f"{API}/schedules", json={
        "name": "To Delete",
        "report_type": "monthly_summary",
        "cron_expression": "0 9 1 * *",
    })
    sid = res.json()["id"]
    assert auth_client.delete(f"{API}/schedules/{sid}").status_code == 204


def test_update_schedule_not_found(auth_client):
    response = auth_client.put(f"{API}/schedules/99999", json={"name": "X"})
    assert response.status_code == 404


def test_delete_schedule_not_found(auth_client):
    assert auth_client.delete(f"{API}/schedules/99999").status_code == 404
