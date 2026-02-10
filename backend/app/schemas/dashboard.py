from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_projects: int
    active_projects: int
    total_engineers: int
    available_engineers: int
    pending_orders: int
    active_contracts: int
    unpaid_invoices: int
    pending_jobs: int
