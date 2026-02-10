from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MatchingResult(Base):
    __tablename__ = "matching_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    engineer_id: Mapped[int] = mapped_column(Integer, ForeignKey("engineers.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    skill_match_rate: Mapped[float] = mapped_column(Float, nullable=False)
    rate_match: Mapped[bool] = mapped_column(Boolean, nullable=False)
    availability_match: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime, default=func.now())

    project = relationship("Project", backref="matching_results")
    engineer = relationship("Engineer", backref="matching_results")
