from datetime import datetime
from pydantic import BaseModel


class ReportGenerateRequest(BaseModel):
    report_type: str = "monthly_summary"
    year: int
    month: int


class ReportGenerateResponse(BaseModel):
    file_name: str
    report_type: str
    year: int
    month: int


class ReportScheduleCreate(BaseModel):
    name: str
    report_type: str
    cron_expression: str
    recipients: list[str] | None = None
    output_format: str = "excel"
    is_active: bool = True


class ReportScheduleUpdate(BaseModel):
    name: str | None = None
    report_type: str | None = None
    cron_expression: str | None = None
    recipients: list[str] | None = None
    output_format: str | None = None
    is_active: bool | None = None


class ReportScheduleResponse(BaseModel):
    id: int
    name: str
    report_type: str
    cron_expression: str
    recipients: list[str] | None = None
    output_format: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
