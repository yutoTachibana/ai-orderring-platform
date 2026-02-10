from datetime import datetime
from pydantic import BaseModel


class MatchingResultResponse(BaseModel):
    id: int
    project_id: int
    engineer_id: int
    score: float
    skill_match_rate: float
    rate_match: bool
    availability_match: bool
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchingRequest(BaseModel):
    project_id: int
