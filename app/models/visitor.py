"""Visitor, ParkingSpace, Vehicle, VisitorParking models."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import TimestampCreatedMixin, TimestampMixin
from app.models._tenant import TenantModel

if TYPE_CHECKING:
    from app.models.catalog import DocumentType, ParkingSpaceType, VehicleType
    from app.models.core import Property, User


class VisitorLog(TenantModel, TimestampCreatedMixin, Base):
    __tablename__ = "visitor_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False,
    )
    visitor_name: Mapped[str] = mapped_column(String(150), nullable=False)
    document_type_id: Mapped[Optional[int]] = mapped_column(ForeignKey("document_types.id"))
    document_number: Mapped[Optional[str]] = mapped_column(String(50))
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False)
    vehicle_plate: Mapped[Optional[str]] = mapped_column(String(20))
    authorized_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"),
    )
    registered_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"),
    )
    entry_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    exit_time: Mapped[Optional[datetime]] = mapped_column()
    notes: Mapped[Optional[str]] = mapped_column(Text)

    property: Mapped["Property"] = relationship(lazy="selectin")
    document_type: Mapped[Optional["DocumentType"]] = relationship(lazy="joined")
    authorized_user: Mapped[Optional["User"]] = relationship(
        foreign_keys=[authorized_by], lazy="selectin",
    )
    registered_user: Mapped[Optional["User"]] = relationship(
        foreign_keys=[registered_by], lazy="selectin",
    )
    parking: Mapped[list["VisitorParking"]] = relationship(back_populates="visitor_log", lazy="selectin")


class ParkingSpace(TenantModel, TimestampCreatedMixin, Base):
    __tablename__ = "parking_spaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    space_number: Mapped[str] = mapped_column(String(20), nullable=False)
    parking_space_type_id: Mapped[int] = mapped_column(
        ForeignKey("parking_space_types.id"), nullable=False,
    )
    property_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="SET NULL"),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("condominium_id", "space_number"),)

    parking_type: Mapped["ParkingSpaceType"] = relationship(lazy="joined")
    property: Mapped[Optional["Property"]] = relationship(lazy="selectin")


class Vehicle(TenantModel, TimestampMixin, Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False,
    )
    license_plate: Mapped[str] = mapped_column(String(20), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(50))
    model: Mapped[Optional[str]] = mapped_column(String(50))
    color: Mapped[Optional[str]] = mapped_column(String(30))
    vehicle_type_id: Mapped[int] = mapped_column(ForeignKey("vehicle_types.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("condominium_id", "license_plate"),)

    vehicle_type: Mapped["VehicleType"] = relationship(lazy="joined")
    property: Mapped["Property"] = relationship(lazy="selectin")


class VisitorParking(TimestampMixin, Base):
    __tablename__ = "visitor_parking"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    visitor_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visitor_logs.id", ondelete="CASCADE"), nullable=False,
    )
    parking_space_id: Mapped[int] = mapped_column(
        ForeignKey("parking_spaces.id", ondelete="RESTRICT"), nullable=False,
    )
    entry_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    exit_time: Mapped[Optional[datetime]] = mapped_column()
    hourly_rate: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)

    visitor_log: Mapped["VisitorLog"] = relationship(back_populates="parking")
    parking_space: Mapped["ParkingSpace"] = relationship(lazy="joined")
