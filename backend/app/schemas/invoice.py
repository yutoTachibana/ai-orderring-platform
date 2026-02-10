from datetime import date, datetime
from pydantic import BaseModel


class InvoiceBase(BaseModel):
    contract_id: int
    invoice_number: str
    billing_month: date
    working_hours: float
    base_amount: int
    adjustment_amount: int = 0
    tax_amount: int
    total_amount: int
    status: str = "draft"
    notes: str | None = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    working_hours: float | None = None
    base_amount: int | None = None
    adjustment_amount: int | None = None
    tax_amount: int | None = None
    total_amount: int | None = None
    status: str | None = None
    notes: str | None = None


class InvoiceResponse(InvoiceBase):
    id: int
    sent_at: datetime | None = None
    paid_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
