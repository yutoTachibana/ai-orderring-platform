from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.engineer import Engineer, AvailabilityStatus
from app.models.order import Order, OrderStatus
from app.models.contract import Contract, ContractStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.automation import ProcessingJob, JobStatus
from app.schemas.dashboard import DashboardStats
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
