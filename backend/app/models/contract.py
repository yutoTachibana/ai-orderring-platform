import enum

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ContractType(str, enum.Enum):
    quasi_delegation = "quasi_delegation"
    contract = "contract"
    dispatch = "dispatch"


class ContractStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    expired = "expired"
    terminated = "terminated"


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    contract_number: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    contract_type: Mapped[ContractType] = mapped_column(SAEnum(ContractType), nullable=False)
    engineer_id: Mapped[int] = mapped_column(Integer, ForeignKey("engineers.id"), nullable=False)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    start_date = mapped_column(Date, nullable=False)
    end_date = mapped_column(Date, nullable=False)
    monthly_rate: Mapped[int] = mapped_column(Integer, nullable=False)  # JPY
    min_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[ContractStatus] = mapped_column(SAEnum(ContractStatus), default=ContractStatus.draft)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime, default=func.now())
    updated_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    order = relationship("Order", backref="contracts")
    engineer = relationship("Engineer", backref="contracts")
    project = relationship("Project", backref="contracts")
