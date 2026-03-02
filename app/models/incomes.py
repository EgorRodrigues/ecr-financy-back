from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Numeric, Text, func
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CustomArray


class Income(Base):
    __tablename__ = "incomes"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    receipt_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    interest: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    fine: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    discount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    total_received: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    category_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    subcategory_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    cost_center_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    contact_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    document: Mapped[str | None] = mapped_column(Text, nullable=True)
    receiving_method: Mapped[str | None] = mapped_column(Text, nullable=True)
    account_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    competence: Mapped[str | None] = mapped_column(Text, nullable=True)
    project: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(CustomArray(Text), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    transfer_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
