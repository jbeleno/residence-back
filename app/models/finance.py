"""Finance models: ChargeType, Invoice, Payment."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean, CheckConstraint, Date, ForeignKey, Integer, Numeric, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import TimestampCreatedMixin, TimestampMixin
from app.models._tenant import TenantModel

if TYPE_CHECKING:
    from app.models.catalog import ChargeCategory, PaymentMethod, PaymentStatus
    from app.models.core import Property


class ChargeType(TenantModel, TimestampCreatedMixin, Base):
    __tablename__ = "charge_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # NOTE: condominium_id inherited from TenantModel but nullable in original schema
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    charge_category_id: Mapped[int] = mapped_column(ForeignKey("charge_categories.id"), nullable=False)
    default_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    charge_category: Mapped["ChargeCategory"] = relationship(lazy="joined")


class Invoice(TenantModel, TimestampMixin, Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False,
    )
    charge_type_id: Mapped[int] = mapped_column(
        ForeignKey("charge_types.id", ondelete="RESTRICT"), nullable=False,
    )
    payment_status_id: Mapped[int] = mapped_column(ForeignKey("payment_statuses.id"), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period: Mapped[Optional[str]] = mapped_column(String(7))
    paid_at: Mapped[Optional[datetime]] = mapped_column()

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_amount_positive"),
        CheckConstraint("balance >= 0", name="chk_balance_not_negative"),
    )

    property: Mapped["Property"] = relationship(lazy="selectin")
    charge_type: Mapped["ChargeType"] = relationship(lazy="joined")
    payment_status: Mapped["PaymentStatus"] = relationship(lazy="joined")
    payments: Mapped[list["Payment"]] = relationship(back_populates="invoice", lazy="selectin")


class Payment(TimestampCreatedMixin, Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False,
    )
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method_id: Mapped[int] = mapped_column(ForeignKey("payment_methods.id"), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    received_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"),
    )
    payment_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (CheckConstraint("amount_paid > 0", name="chk_payment_positive"),)

    invoice: Mapped["Invoice"] = relationship(back_populates="payments")
    payment_method: Mapped["PaymentMethod"] = relationship(lazy="joined")
