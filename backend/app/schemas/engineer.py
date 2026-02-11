from datetime import datetime
from pydantic import BaseModel
from app.schemas.skill_tag import SkillTagResponse
from app.schemas.company import CompanyResponse


class EngineerBase(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    company_id: int | None = None
    employment_type: str = "proper"
    hourly_rate: int | None = None
    monthly_rate: int | None = None
    availability_status: str = "available"
    years_of_experience: int | None = None
    notes: str | None = None
    is_active: bool = True


class EngineerCreate(EngineerBase):
    skill_ids: list[int] = []


class EngineerUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    company_id: int | None = None
    employment_type: str | None = None
    hourly_rate: int | None = None
    monthly_rate: int | None = None
    availability_status: str | None = None
    years_of_experience: int | None = None
    notes: str | None = None
    is_active: bool | None = None
    skill_ids: list[int] | None = None


class EngineerResponse(EngineerBase):
    id: int
    employment_type: str
    subcontracting_tier: int
    company: CompanyResponse | None = None
    skills: list[SkillTagResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
