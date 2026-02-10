from datetime import datetime
from pydantic import BaseModel


class CompanyBase(BaseModel):
    name: str
    company_type: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    notes: str | None = None
    is_active: bool = True


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None
    company_type: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
