from datetime import date, datetime
from pydantic import BaseModel
from app.schemas.skill_tag import SkillTagResponse
from app.schemas.company import CompanyResponse


class ProjectBase(BaseModel):
    name: str
    description: str | None = None
    client_company_id: int | None = None
    status: str = "draft"
    subcontracting_tier_limit: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: int | None = None
    required_headcount: int | None = None
    notes: str | None = None


class ProjectCreate(ProjectBase):
    skill_ids: list[int] = []


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    client_company_id: int | None = None
    status: str | None = None
    subcontracting_tier_limit: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: int | None = None
    required_headcount: int | None = None
    notes: str | None = None
    skill_ids: list[int] | None = None


class ProjectResponse(ProjectBase):
    id: int
    client_company: CompanyResponse | None = None
    required_skills: list[SkillTagResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
