from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Date, Numeric, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CreditCardInvoice(Base):
    __tablename__ = "credit_card_invoices"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="open")
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    interest: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    fine: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    discount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    total_paid: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    expense_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "account_id", "period_start", "period_end", name="uq_credit_card_invoices_period"
        ),
    )
