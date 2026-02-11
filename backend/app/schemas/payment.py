from datetime import date, datetime
from pydantic import BaseModel


class PaymentResponse(BaseModel):
    id: int
    invoice_id: int | None = None
    payment_date: date
    amount: int
    payer_name: str | None = None
    reference_number: str | None = None
    bank_name: str | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentManualMatch(BaseModel):
    invoice_id: int


class ReconciliationSummary(BaseModel):
    total_payments: int
    matched: int
    unmatched: int
    confirmed: int
    total_amount: int
    matched_amount: int
