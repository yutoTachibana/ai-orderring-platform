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


class EmploymentType(str, enum.Enum):
    proper = "proper"                          # 自社正社員（プロパー）
    first_tier_proper = "first_tier_proper"    # 一社先プロパー
    freelancer = "freelancer"                  # 個人事業主（フリーランス）
    first_tier_freelancer = "first_tier_freelancer"  # 一社先個人事業主


class Engineer(Base):
    __tablename__ = "engineers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    company_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("companies.id"), nullable=True)
    hourly_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)  # JPY
    monthly_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)  # JPY
    employment_type: Mapped[EmploymentType] = mapped_column(
        SAEnum(EmploymentType), default=EmploymentType.proper, server_default="proper"
    )
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

    @property
    def subcontracting_tier(self) -> int:
        """商流の深さ（tier）を動的算出する。

        - proper（自社正社員）→ 0
        - first_tier_proper（一社先プロパー）→ 1
        - freelancer + company_id なし（直接契約フリーランス）→ 1
        - first_tier_freelancer（一社先個人事業主）→ 2
        - freelancer + company_id あり（パートナー企業経由）→ 2
        """
        if self.employment_type == EmploymentType.proper:
            return 0
        if self.employment_type == EmploymentType.first_tier_proper:
            return 1
        if self.employment_type == EmploymentType.first_tier_freelancer:
            return 2
        # freelancer
        if self.company_id is not None:
            return 2
        return 1
