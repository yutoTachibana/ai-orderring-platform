from datetime import datetime
from pydantic import BaseModel


class OrderBase(BaseModel):
    quotation_id: int
    order_number: str
    status: str = "pending"
    notes: str | None = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None


class OrderResponse(OrderBase):
    id: int
    confirmed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
