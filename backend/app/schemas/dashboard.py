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


class MonthlyTrendItem(BaseModel):
    month: str
    new_projects: int
    new_orders: int
    revenue: int
    invoice_total: int


class AssignedEngineerInfo(BaseModel):
    engineer_id: int
    name: str
    project_name: str | None = None
    monthly_rate: int | None = None
    end_date: str | None = None


class EngineerUtilization(BaseModel):
    available: int
    assigned: int
    unavailable: int
    assigned_engineers: list[AssignedEngineerInfo]
