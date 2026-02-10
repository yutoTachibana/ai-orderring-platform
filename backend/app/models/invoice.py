import enum

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    paid = "paid"
    overdue = "overdue"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    contract_id: Mapped[int] = mapped_column(Integer, ForeignKey("contracts.id"), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    billing_month = mapped_column(Date, nullable=False)
    working_hours: Mapped[float] = mapped_column(Float, nullable=False)
    base_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # JPY
    adjustment_amount: Mapped[int] = mapped_column(Integer, default=0)  # JPY
    tax_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # JPY
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # JPY
    status: Mapped[InvoiceStatus] = mapped_column(SAEnum(InvoiceStatus), default=InvoiceStatus.draft)
    sent_at = mapped_column(DateTime, nullable=True)
    paid_at = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime, default=func.now())
    updated_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    contract = relationship("Contract", backref="invoices")
