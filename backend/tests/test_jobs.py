"""Tests for /api/v1/jobs endpoints."""

from unittest.mock import patch

from app.models.automation import JobStatus, ProcessingJob, ProcessingLog


# ---------------------------------------------------------------------------
# GET /api/v1/jobs  (list - no auth required)
# ---------------------------------------------------------------------------


def test_list_jobs_empty(client):
    """The jobs list endpoint does NOT require auth."""
    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_jobs_with_data(client, db):
    job = ProcessingJob(status=JobStatus.received)
    db.add(job)
    db.commit()

    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


def test_list_jobs_with_status_filter(client, db):
    """Filtering by status should return only matching jobs."""
    j1 = ProcessingJob(status=JobStatus.received)
    j2 = ProcessingJob(status=JobStatus.pending_approval)
    j3 = ProcessingJob(status=JobStatus.completed)
    j4 = ProcessingJob(status=JobStatus.pending_approval)
    db.add_all([j1, j2, j3, j4])
    db.commit()

    # Filter for pending_approval
    response = client.get("/api/v1/jobs", params={"status": "pending_approval"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    for item in data["items"]:
        assert item["status"] == "pending_approval"

    # Filter for completed
    response = client.get("/api/v1/jobs", params={"status": "completed"})
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "completed"

    # Filter for a status with no matches
    response = client.get("/api/v1/jobs", params={"status": "failed"})
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_jobs_pagination(client, db):
    """Pagination should slice results correctly and return metadata."""
    # Create 25 jobs
    for i in range(25):
        db.add(ProcessingJob(status=JobStatus.received))
    db.commit()

    # Default: page=1, per_page=20
    response = client.get("/api/v1/jobs")
    data = response.json()
    assert data["total"] == 25
    assert data["page"] == 1
    assert data["per_page"] == 20
    assert data["pages"] == 2
    assert len(data["items"]) == 20

    # Page 2 should have the remaining 5
    response = client.get("/api/v1/jobs", params={"page": 2, "per_page": 20})
    data = response.json()
    assert data["total"] == 25
    assert data["page"] == 2
    assert len(data["items"]) == 5

    # Custom per_page
    response = client.get("/api/v1/jobs", params={"page": 1, "per_page": 10})
    data = response.json()
    assert data["total"] == 25
    assert data["per_page"] == 10
    assert data["pages"] == 3
    assert len(data["items"]) == 10


def test_list_jobs_includes_logs(client, db):
    """List endpoint should include logs for each job via eager loading."""
    job = ProcessingJob(status=JobStatus.parsing)
    db.add(job)
    db.flush()

    log1 = ProcessingLog(job_id=job.id, step_name="受信", status="completed", message="OK")
    log2 = ProcessingLog(job_id=job.id, step_name="解析", status="started", message="Processing")
    db.add_all([log1, log2])
    db.commit()

    response = client.get("/api/v1/jobs")
    data = response.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert len(item["logs"]) == 2


# ---------------------------------------------------------------------------
# GET /api/v1/jobs/{job_id}  (detail - auth required)
# ---------------------------------------------------------------------------


def test_get_job_not_found(auth_client):
    response = auth_client.get("/api/v1/jobs/99999")
    assert response.status_code == 404


def test_get_job_unauthenticated(client, db):
    """The job detail endpoint requires authentication."""
    job = ProcessingJob(status=JobStatus.received)
    db.add(job)
    db.commit()
    db.refresh(job)

    response = client.get(f"/api/v1/jobs/{job.id}")
    assert response.status_code == 401


def test_get_job_detail(auth_client, db):
    """Successfully retrieve a single job by ID."""
    job = ProcessingJob(
        status=JobStatus.pending_approval,
        slack_channel_id="C12345",
        slack_message_id="msg_001",
        excel_file_path="/uploads/test.xlsx",
        result={"案件名": "Detail Test Project", "単価": "600000"},
    )
    db.add(job)
    db.flush()

    log = ProcessingLog(
        job_id=job.id,
        step_name="受信",
        status="completed",
        message="ファイル受信完了",
    )
    db.add(log)
    db.commit()
    db.refresh(job)

    response = auth_client.get(f"/api/v1/jobs/{job.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job.id
    assert data["status"] == "pending_approval"
    assert data["slack_channel_id"] == "C12345"
    assert data["slack_message_id"] == "msg_001"
    assert data["excel_file_path"] == "/uploads/test.xlsx"
    assert data["result"]["案件名"] == "Detail Test Project"
    assert data["result"]["単価"] == "600000"
    assert len(data["logs"]) == 1
    assert data["logs"][0]["step_name"] == "受信"


# ---------------------------------------------------------------------------
# POST /api/v1/jobs/{job_id}/approve  (approve/reject - auth required)
# ---------------------------------------------------------------------------


def test_approve_job_not_found(auth_client):
    response = auth_client.post(
        "/api/v1/jobs/99999/approve",
        json={"approved": True},
    )
    assert response.status_code == 404


def test_approve_job_wrong_status(auth_client, db):
    """A job that is not in pending_approval cannot be approved."""
    job = ProcessingJob(status=JobStatus.received)
    db.add(job)
    db.commit()
    db.refresh(job)

    response = auth_client.post(
        f"/api/v1/jobs/{job.id}/approve",
        json={"approved": True},
    )
    assert response.status_code == 400


def test_approve_job_unauthenticated(client, db):
    """The approve endpoint requires authentication."""
    job = ProcessingJob(status=JobStatus.pending_approval)
    db.add(job)
    db.commit()
    db.refresh(job)

    response = client.post(
        f"/api/v1/jobs/{job.id}/approve",
        json={"approved": True},
    )
    assert response.status_code == 401


@patch("app.services.order_registration.register_order_from_job", return_value={"company": {"name": "TestCo", "new": True}})
@patch("app.services.mcp_executor.execute_mcp_input", return_value={"success": True, "confirmation_id": "CONF-001"})
def test_approve_job_successfully(mock_mcp, mock_register, auth_client, db):
    """Approving a pending_approval job should move it to completed."""
    job = ProcessingJob(
        status=JobStatus.pending_approval,
        result={"案件名": "Approval Test", "発注先": "TestCo"},
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    response = auth_client.post(
        f"/api/v1/jobs/{job.id}/approve",
        json={"approved": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["approved_by"] is not None
    assert data["approved_at"] is not None
    mock_register.assert_called_once()
    mock_mcp.assert_called_once()


@patch("app.services.order_registration.register_order_from_job", side_effect=Exception("Registration failed"))
@patch("app.services.mcp_executor.execute_mcp_input", return_value={})
def test_approve_job_falls_back_to_failed_on_error(mock_mcp, mock_register, auth_client, db):
    """When synchronous execution raises an error during approval, the job
    should be marked as failed."""
    job = ProcessingJob(
        status=JobStatus.pending_approval,
        result={"案件名": "Will Fail"},
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    response = auth_client.post(
        f"/api/v1/jobs/{job.id}/approve",
        json={"approved": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert "処理エラー" in data["error_message"]


def test_reject_job_successfully(auth_client, db):
    """Rejecting a pending_approval job should move it to failed."""
    job = ProcessingJob(
        status=JobStatus.pending_approval,
        result={"案件名": "Rejection Test"},
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    response = auth_client.post(
        f"/api/v1/jobs/{job.id}/approve",
        json={"approved": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert "却下" in data["error_message"]
    assert data["approved_by"] is not None
    assert data["approved_at"] is not None


def test_reject_job_wrong_status(auth_client, db):
    """A job that is not in pending_approval cannot be rejected."""
    job = ProcessingJob(status=JobStatus.completed)
    db.add(job)
    db.commit()
    db.refresh(job)

    response = auth_client.post(
        f"/api/v1/jobs/{job.id}/approve",
        json={"approved": False},
    )
    assert response.status_code == 400
    assert "承認待ち" in response.json()["detail"]


def test_list_jobs_with_status_filter_and_pagination(client, db):
    """Combine status filter with pagination."""
    # Create 15 pending_approval jobs and 5 completed jobs
    for _ in range(15):
        db.add(ProcessingJob(status=JobStatus.pending_approval))
    for _ in range(5):
        db.add(ProcessingJob(status=JobStatus.completed))
    db.commit()

    # Filter for pending_approval with per_page=10
    response = client.get("/api/v1/jobs", params={
        "status": "pending_approval",
        "page": 1,
        "per_page": 10,
    })
    data = response.json()
    assert data["total"] == 15
    assert data["pages"] == 2
    assert len(data["items"]) == 10

    # Page 2
    response = client.get("/api/v1/jobs", params={
        "status": "pending_approval",
        "page": 2,
        "per_page": 10,
    })
    data = response.json()
    assert len(data["items"]) == 5
