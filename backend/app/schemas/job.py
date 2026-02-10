from datetime import datetime
from typing import Any
from pydantic import BaseModel


class ProcessingLogResponse(BaseModel):
    id: int
    job_id: int
    step_name: str
    status: str
    message: str
    screenshot_path: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    id: int
    slack_message_id: str | None = None
    slack_channel_id: str | None = None
    excel_file_path: str | None = None
    status: str
    assigned_system: str | None = None
    approved_by: int | None = None
    approved_at: datetime | None = None
    result: dict[str, Any] | None = None
    error_message: str | None = None
    logs: list[ProcessingLogResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobApproveRequest(BaseModel):
    approved: bool
