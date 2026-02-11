"""Tests for /api/v1/dashboard endpoints."""

from datetime import date

from app.models.automation import ProcessingJob, ProcessingLog, JobStatus
from app.models.company import Company, CompanyType
from app.models.contract import Contract, ContractStatus, ContractType
from app.models.engineer import Engineer, AvailabilityStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.order import Order, OrderStatus
from app.models.project import Project, ProjectStatus
from app.models.quotation import Quotation, QuotationStatus


EXPECTED_STATS_KEYS = {
    "total_projects",
    "active_projects",
    "total_engineers",
    "available_engineers",
    "pending_orders",
    "active_contracts",
    "unpaid_invoices",
    "pending_jobs",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_full_chain(db, *, order_status=OrderStatus.pending,
                       contract_status=ContractStatus.active,
                       invoice_status=InvoiceStatus.sent):
    """Create a full Company -> Project -> Engineer -> Quotation -> Order ->
    Contract -> Invoice chain and return all created objects."""
    company = Company(name="Test Corp", company_type=CompanyType.client)
    db.add(company)
    db.flush()

    project = Project(
        name="Test Project",
        client_company_id=company.id,
        status=ProjectStatus.in_progress,
    )
    db.add(project)
    db.flush()

    engineer = Engineer(
        full_name="Taro Yamada",
        availability_status=AvailabilityStatus.available,
    )
    db.add(engineer)
    db.flush()

    quotation = Quotation(
        project_id=project.id,
        engineer_id=engineer.id,
        unit_price=500000,
        estimated_hours=160,
        total_amount=500000,
        status=QuotationStatus.approved,
    )
    db.add(quotation)
    db.flush()

    order = Order(
        quotation_id=quotation.id,
        order_number="ORD-20260101-001",
        status=order_status,
    )
    db.add(order)
    db.flush()

    contract = Contract(
        order_id=order.id,
        contract_number="CTR-001",
        contract_type=ContractType.quasi_delegation,
        engineer_id=engineer.id,
        project_id=project.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        monthly_rate=500000,
        status=contract_status,
    )
    db.add(contract)
    db.flush()

    invoice = Invoice(
        contract_id=contract.id,
        invoice_number="INV-001",
        billing_month=date(2026, 1, 1),
        working_hours=160.0,
        base_amount=500000,
        adjustment_amount=0,
        tax_amount=50000,
        total_amount=550000,
        status=invoice_status,
    )
    db.add(invoice)
    db.commit()

    return {
        "company": company,
        "project": project,
        "engineer": engineer,
        "quotation": quotation,
        "order": order,
        "contract": contract,
        "invoice": invoice,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/stats
# ---------------------------------------------------------------------------


def test_dashboard_stats_unauthenticated(client):
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 401


def test_dashboard_stats_structure(auth_client):
    response = auth_client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == EXPECTED_STATS_KEYS
    # With an empty DB every counter should be zero
    for key in EXPECTED_STATS_KEYS:
        assert isinstance(data[key], int)
        assert data[key] == 0


def test_dashboard_stats_with_data(auth_client, db):
    """Create real data and verify the stats endpoint returns correct counts."""
    chain = _create_full_chain(db)

    # Also add a processing job in pending_approval (should count as pending)
    job = ProcessingJob(status=JobStatus.pending_approval)
    db.add(job)
    db.commit()

    response = auth_client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["total_projects"] == 1
    assert data["active_projects"] == 1          # ProjectStatus.in_progress
    assert data["total_engineers"] == 1
    assert data["available_engineers"] == 1       # AvailabilityStatus.available
    assert data["pending_orders"] == 1            # OrderStatus.pending
    assert data["active_contracts"] == 1          # ContractStatus.active
    assert data["unpaid_invoices"] == 1           # InvoiceStatus.sent
    assert data["pending_jobs"] == 1              # JobStatus.pending_approval


def test_dashboard_stats_counts_only_matching_statuses(auth_client, db):
    """Stats should only count items with the expected statuses.
    E.g. completed projects are NOT counted as active_projects."""
    company = Company(name="Corp A", company_type=CompanyType.client)
    db.add(company)
    db.flush()

    # 2 projects: 1 in_progress (active), 1 completed (not active)
    p1 = Project(name="Active", client_company_id=company.id, status=ProjectStatus.in_progress)
    p2 = Project(name="Done", client_company_id=company.id, status=ProjectStatus.completed)
    db.add_all([p1, p2])
    db.flush()

    # 3 engineers: 1 available, 1 assigned, 1 unavailable
    e1 = Engineer(full_name="Available", availability_status=AvailabilityStatus.available)
    e2 = Engineer(full_name="Assigned", availability_status=AvailabilityStatus.assigned)
    e3 = Engineer(full_name="Unavailable", availability_status=AvailabilityStatus.unavailable)
    db.add_all([e1, e2, e3])
    db.flush()

    # Orders: 1 pending, 1 confirmed (not pending)
    q = Quotation(
        project_id=p1.id, engineer_id=e1.id,
        unit_price=400000, estimated_hours=160, total_amount=400000,
        status=QuotationStatus.approved,
    )
    db.add(q)
    db.flush()
    o1 = Order(quotation_id=q.id, order_number="ORD-001", status=OrderStatus.pending)
    o2 = Order(quotation_id=q.id, order_number="ORD-002", status=OrderStatus.confirmed)
    db.add_all([o1, o2])
    db.flush()

    # Contracts: 1 active, 1 expired
    c1 = Contract(
        order_id=o1.id, contract_number="CTR-A1", contract_type=ContractType.quasi_delegation,
        engineer_id=e1.id, project_id=p1.id,
        start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        monthly_rate=400000, status=ContractStatus.active,
    )
    c2 = Contract(
        order_id=o2.id, contract_number="CTR-A2", contract_type=ContractType.contract,
        engineer_id=e2.id, project_id=p2.id,
        start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        monthly_rate=350000, status=ContractStatus.expired,
    )
    db.add_all([c1, c2])
    db.flush()

    # Invoices: 1 sent (unpaid), 1 paid (not unpaid), 1 overdue (unpaid)
    inv1 = Invoice(
        contract_id=c1.id, invoice_number="INV-A1",
        billing_month=date(2026, 1, 1), working_hours=160.0,
        base_amount=400000, tax_amount=40000, total_amount=440000,
        status=InvoiceStatus.sent,
    )
    inv2 = Invoice(
        contract_id=c1.id, invoice_number="INV-A2",
        billing_month=date(2026, 2, 1), working_hours=160.0,
        base_amount=400000, tax_amount=40000, total_amount=440000,
        status=InvoiceStatus.paid,
    )
    inv3 = Invoice(
        contract_id=c2.id, invoice_number="INV-A3",
        billing_month=date(2025, 12, 1), working_hours=160.0,
        base_amount=350000, tax_amount=35000, total_amount=385000,
        status=InvoiceStatus.overdue,
    )
    db.add_all([inv1, inv2, inv3])

    # Jobs: 1 received, 1 pending_approval, 1 completed, 1 failed
    j1 = ProcessingJob(status=JobStatus.received)
    j2 = ProcessingJob(status=JobStatus.pending_approval)
    j3 = ProcessingJob(status=JobStatus.completed)
    j4 = ProcessingJob(status=JobStatus.failed)
    db.add_all([j1, j2, j3, j4])
    db.commit()

    response = auth_client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["total_projects"] == 2
    assert data["active_projects"] == 1           # only in_progress
    assert data["total_engineers"] == 3
    assert data["available_engineers"] == 1        # only available
    assert data["pending_orders"] == 1             # only pending
    assert data["active_contracts"] == 1           # only active
    assert data["unpaid_invoices"] == 2            # sent + overdue
    assert data["pending_jobs"] == 2               # received + pending_approval


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/recent-activities
# ---------------------------------------------------------------------------


def test_recent_activities_unauthenticated(client):
    """The recent-activities endpoint requires authentication."""
    response = client.get("/api/v1/dashboard/recent-activities")
    assert response.status_code == 401


def test_recent_activities_empty_db(auth_client):
    """With no data, recent-activities should return empty lists."""
    response = auth_client.get("/api/v1/dashboard/recent-activities")
    assert response.status_code == 200
    data = response.json()
    assert "recent_jobs" in data
    assert "recent_projects" in data
    assert "recent_orders" in data
    assert data["recent_jobs"] == []
    assert data["recent_projects"] == []
    assert data["recent_orders"] == []


def test_recent_activities_with_data(auth_client, db):
    """Verify the structure and content of recent activities with real data."""
    chain = _create_full_chain(db)

    # Create a job with logs
    job = ProcessingJob(
        status=JobStatus.pending_approval,
        result={"案件名": "Test Activity Project"},
    )
    db.add(job)
    db.flush()
    log = ProcessingLog(
        job_id=job.id,
        step_name="受信",
        status="completed",
        message="ファイル受信: test.xlsx",
    )
    db.add(log)
    db.commit()

    response = auth_client.get("/api/v1/dashboard/recent-activities")
    assert response.status_code == 200
    data = response.json()

    # Check recent_jobs
    assert len(data["recent_jobs"]) == 1
    rj = data["recent_jobs"][0]
    assert rj["id"] == job.id
    assert rj["status"] == "pending_approval"
    assert rj["project_name"] == "Test Activity Project"
    assert rj["created_at"] is not None
    # Verify logs are included
    assert len(rj["logs"]) == 1
    assert rj["logs"][0]["step"] == "受信"
    assert rj["logs"][0]["status"] == "completed"

    # Check recent_projects
    assert len(data["recent_projects"]) == 1
    rp = data["recent_projects"][0]
    assert rp["id"] == chain["project"].id
    assert rp["name"] == "Test Project"
    assert rp["status"] == "in_progress"
    assert rp["client"] == "Test Corp"

    # Check recent_orders
    assert len(data["recent_orders"]) == 1
    ro = data["recent_orders"][0]
    assert ro["id"] == chain["order"].id
    assert ro["order_number"] == "ORD-20260101-001"
    assert ro["status"] == "pending"


def test_recent_activities_limits_to_five(auth_client, db):
    """recent-activities should return at most 5 items per category."""
    company = Company(name="Bulk Corp", company_type=CompanyType.client)
    db.add(company)
    db.flush()

    # Create 7 projects
    for i in range(7):
        db.add(Project(
            name=f"Project {i}",
            client_company_id=company.id,
            status=ProjectStatus.draft,
        ))

    # Create 7 jobs
    for i in range(7):
        db.add(ProcessingJob(status=JobStatus.received))

    db.commit()

    response = auth_client.get("/api/v1/dashboard/recent-activities")
    assert response.status_code == 200
    data = response.json()

    assert len(data["recent_projects"]) == 5
    assert len(data["recent_jobs"]) == 5
