import enum

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

project_required_skills = Table(
    "project_required_skills",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("skill_tag_id", Integer, ForeignKey("skill_tags.id"), primary_key=True),
)


class ProjectStatus(str, enum.Enum):
    draft = "draft"
    open = "open"
    in_progress = "in_progress"
    completed = "completed"
    closed = "closed"


class SubcontractingTierLimit(str, enum.Enum):
    proper_only = "proper_only"    # プロパーのみ
    first_tier = "first_tier"      # 一社先まで
    second_tier = "second_tier"    # 二社先まで
    no_restriction = "no_restriction"  # 制限なし


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(SAEnum(ProjectStatus), default=ProjectStatus.draft)
    start_date = mapped_column(Date, nullable=True)
    end_date = mapped_column(Date, nullable=True)
    budget: Mapped[int | None] = mapped_column(Integer, nullable=True)  # JPY
    required_headcount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subcontracting_tier_limit: Mapped[SubcontractingTierLimit | None] = mapped_column(
        SAEnum(SubcontractingTierLimit), nullable=True, default=None
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime, default=func.now())
    updated_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    client_company = relationship("Company", backref="projects")
    required_skills = relationship("SkillTag", secondary=project_required_skills, backref="projects")
