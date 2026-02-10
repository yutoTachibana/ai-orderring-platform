from datetime import datetime
from pydantic import BaseModel


class QuotationBase(BaseModel):
    project_id: int
    engineer_id: int
    unit_price: int
    estimated_hours: int
    total_amount: int
    status: str = "draft"
    notes: str | None = None


class QuotationCreate(QuotationBase):
    pass


class QuotationUpdate(BaseModel):
    unit_price: int | None = None
    estimated_hours: int | None = None
    total_amount: int | None = None
    status: str | None = None
    notes: str | None = None


class QuotationResponse(QuotationBase):
    id: int
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
