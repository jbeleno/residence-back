"""Amenities and bookings models."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String, Text, Time,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import TimestampMixin
from app.models._tenant import TenantModel

if TYPE_CHECKING:
    from app.models.core import Property, User
    from app.models.catalog import BookingStatus


class Amenity(TenantModel, TimestampMixin, Base):
    __tablename__ = "amenities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    capacity: Mapped[Optional[int]] = mapped_column(Integer)
    hourly_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0, server_default="0")
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    min_hours: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    max_hours: Mapped[int] = mapped_column(Integer, default=8, server_default="8")
    available_from: Mapped[Optional[str]] = mapped_column(Time)
    available_until: Mapped[Optional[str]] = mapped_column(Time)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    bookings: Mapped[list["AmenityBooking"]] = relationship(back_populates="amenity", lazy="selectin")


class AmenityBooking(TimestampMixin, Base):
    __tablename__ = "amenity_bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amenity_id: Mapped[int] = mapped_column(ForeignKey("amenities.id", ondelete="CASCADE"), nullable=False)
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False,
    )
    booked_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    booking_status_id: Mapped[int] = mapped_column(ForeignKey("booking_statuses.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(nullable=False)
    end_time: Mapped[datetime] = mapped_column(nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"),
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column()
    cancelled_at: Mapped[Optional[datetime]] = mapped_column()
    cancelled_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    __table_args__ = (CheckConstraint("end_time > start_time", name="chk_booking_times"),)

    amenity: Mapped["Amenity"] = relationship(back_populates="bookings", lazy="joined")
    booking_status: Mapped["BookingStatus"] = relationship(lazy="joined")
    property: Mapped["Property"] = relationship(lazy="selectin")
    user: Mapped["User"] = relationship(foreign_keys=[booked_by], lazy="joined")
