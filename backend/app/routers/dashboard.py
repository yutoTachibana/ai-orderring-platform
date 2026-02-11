from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, extract
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.engineer import Engineer, AvailabilityStatus
from app.models.order import Order, OrderStatus
from app.models.contract import Contract, ContractStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.automation import ProcessingJob, ProcessingLog, JobStatus
from app.schemas.dashboard import (
    DashboardStats,
    MonthlyTrendItem,
    AssignedEngineerInfo,
    EngineerUtilization,
)
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("/stats", response_model=DashboardStats, summary="ダッシュボード統計")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.status == ProjectStatus.in_progress).count()

    total_engineers = db.query(Engineer).count()
    available_engineers = db.query(Engineer).filter(
        Engineer.availability_status == AvailabilityStatus.available
    ).count()

    pending_orders = db.query(Order).filter(Order.status == OrderStatus.pending).count()

    active_contracts = db.query(Contract).filter(Contract.status == ContractStatus.active).count()

    unpaid_invoices = db.query(Invoice).filter(
        Invoice.status.in_([InvoiceStatus.sent, InvoiceStatus.overdue])
    ).count()

    pending_jobs = db.query(ProcessingJob).filter(
        ProcessingJob.status.in_([
            JobStatus.received,
            JobStatus.parsing,
            JobStatus.routing,
            JobStatus.pending_approval,
            JobStatus.executing,
        ])
    ).count()

    return DashboardStats(
        total_projects=total_projects,
        active_projects=active_projects,
        total_engineers=total_engineers,
        available_engineers=available_engineers,
        pending_orders=pending_orders,
        active_contracts=active_contracts,
        unpaid_invoices=unpaid_invoices,
        pending_jobs=pending_jobs,
    )


@router.get("/recent-activities", summary="最近のアクティビティ")
def get_recent_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 最近のジョブ（最新5件）
    recent_jobs = (
        db.query(ProcessingJob)
        .options(joinedload(ProcessingJob.logs))
        .order_by(ProcessingJob.created_at.desc())
        .limit(5)
        .all()
    )

    # 最近の案件（最新5件）
    recent_projects = (
        db.query(Project)
        .options(joinedload(Project.client_company))
        .order_by(Project.created_at.desc())
        .limit(5)
        .all()
    )

    # 最近の発注（最新5件）
    recent_orders = (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "recent_jobs": [
            {
                "id": j.id,
                "status": j.status.value,
                "assigned_system": j.assigned_system,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "project_name": (j.result or {}).get("案件名"),
                "mcp_result": (j.result or {}).get("mcp_result"),
                "logs": [
                    {"step": l.step_name, "status": l.status, "message": l.message}
                    for l in sorted(j.logs, key=lambda x: x.id)
                ],
            }
            for j in recent_jobs
        ],
        "recent_projects": [
            {
                "id": p.id,
                "name": p.name,
                "status": p.status.value,
                "client": p.client_company.name if p.client_company else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in recent_projects
        ],
        "recent_orders": [
            {
                "id": o.id,
                "order_number": o.order_number,
                "status": o.status.value,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in recent_orders
        ],
    }


@router.get(
    "/monthly-trends",
    response_model=list[MonthlyTrendItem],
    summary="月次推移データ",
)
def get_monthly_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """過去6ヶ月の月次推移データを返す"""
    today = date.today()
    # Build list of last 6 months (including current month)
    months: list[tuple[int, int]] = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 28)
        # Normalize to first of that month
        d = d.replace(day=1)
        months.append((d.year, d.month))
    # Deduplicate while preserving order
    seen: set[tuple[int, int]] = set()
    unique_months: list[tuple[int, int]] = []
    for m in months:
        if m not in seen:
            seen.add(m)
            unique_months.append(m)
    months = unique_months[-6:]

    results: list[MonthlyTrendItem] = []
    for year, month in months:
        # New projects created this month
        new_projects = (
            db.query(func.count(Project.id))
            .filter(
                extract("year", Project.created_at) == year,
                extract("month", Project.created_at) == month,
            )
            .scalar()
            or 0
        )

        # New orders created this month
        new_orders = (
            db.query(func.count(Order.id))
            .filter(
                extract("year", Order.created_at) == year,
                extract("month", Order.created_at) == month,
            )
            .scalar()
            or 0
        )

        # Revenue: sum of paid invoices for this billing month
        revenue = (
            db.query(func.coalesce(func.sum(Invoice.total_amount), 0))
            .filter(
                Invoice.status == InvoiceStatus.paid,
                extract("year", Invoice.billing_month) == year,
                extract("month", Invoice.billing_month) == month,
            )
            .scalar()
            or 0
        )

        # Invoice total: sum of all invoices for this billing month
        invoice_total = (
            db.query(func.coalesce(func.sum(Invoice.total_amount), 0))
            .filter(
                extract("year", Invoice.billing_month) == year,
                extract("month", Invoice.billing_month) == month,
            )
            .scalar()
            or 0
        )

        results.append(
            MonthlyTrendItem(
                month=f"{year}-{month:02d}",
                new_projects=new_projects,
                new_orders=new_orders,
                revenue=revenue,
                invoice_total=invoice_total,
            )
        )

    return results


@router.get(
    "/engineer-utilization",
    response_model=EngineerUtilization,
    summary="エンジニア稼働状況",
)
def get_engineer_utilization(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """エンジニアの稼働状況分布とアサイン済みエンジニアの詳細を返す"""
    available = (
        db.query(func.count(Engineer.id))
        .filter(Engineer.availability_status == AvailabilityStatus.available)
        .scalar()
        or 0
    )
    assigned = (
        db.query(func.count(Engineer.id))
        .filter(Engineer.availability_status == AvailabilityStatus.assigned)
        .scalar()
        or 0
    )
    unavailable = (
        db.query(func.count(Engineer.id))
        .filter(Engineer.availability_status == AvailabilityStatus.unavailable)
        .scalar()
        or 0
    )

    # Get assigned engineers with their active contract info
    assigned_engineers_query = (
        db.query(Engineer, Contract, Project)
        .outerjoin(Contract, (Contract.engineer_id == Engineer.id) & (Contract.status == ContractStatus.active))
        .outerjoin(Project, Contract.project_id == Project.id)
        .filter(Engineer.availability_status == AvailabilityStatus.assigned)
        .all()
    )

    assigned_engineers: list[AssignedEngineerInfo] = []
    for engineer, contract, project in assigned_engineers_query:
        assigned_engineers.append(
            AssignedEngineerInfo(
                engineer_id=engineer.id,
                name=engineer.full_name,
                project_name=project.name if project else None,
                monthly_rate=contract.monthly_rate if contract else None,
                end_date=contract.end_date.isoformat() if contract and contract.end_date else None,
            )
        )

    return EngineerUtilization(
        available=available,
        assigned=assigned,
        unavailable=unavailable,
        assigned_engineers=assigned_engineers,
    )
