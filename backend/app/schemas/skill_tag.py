from pydantic import BaseModel


class SkillTagBase(BaseModel):
    name: str
    category: str = "other"


class SkillTagCreate(SkillTagBase):
    pass


class SkillTagResponse(SkillTagBase):
    id: int

    model_config = {"from_attributes": True}
