from datetime import date, datetime
from pydantic import BaseModel


class ContractBase(BaseModel):
    order_id: int
    contract_number: str
    contract_type: str
    engineer_id: int
    project_id: int
    start_date: date
    end_date: date
    monthly_rate: int
    min_hours: int | None = None
    max_hours: int | None = None
    status: str = "draft"
    notes: str | None = None


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    contract_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    monthly_rate: int | None = None
    min_hours: int | None = None
    max_hours: int | None = None
    status: str | None = None
    notes: str | None = None


class ContractResponse(ContractBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
