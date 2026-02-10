import enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

engineer_skills = Table(
    "engineer_skills",
    Base.metadata,
    Column("engineer_id", Integer, ForeignKey("engineers.id"), primary_key=True),
    Column("skill_tag_id", Integer, ForeignKey("skill_tags.id"), primary_key=True),
)


class AvailabilityStatus(str, enum.Enum):
    available = "available"
    assigned = "assigned"
    unavailable = "unavailable"


class Engineer(Base):
    __tablename__ = "engineers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    company_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)
    hourly_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)  # JPY
    monthly_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)  # JPY
    availability_status: Mapped[AvailabilityStatus] = mapped_column(
        SAEnum(AvailabilityStatus), default=AvailabilityStatus.available
    )
    years_of_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at = mapped_column(DateTime, default=func.now())
    updated_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    company = relationship("Company", backref="engineers")
    skills = relationship("SkillTag", secondary=engineer_skills, backref="engineers")
