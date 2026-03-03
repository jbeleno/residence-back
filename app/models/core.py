"""Core domain models: Condominium, Role, User, UserCondominiumRole,
Property, UserProperty, UserDevice."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean, Date, ForeignKey, Integer, Numeric, String, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import SoftDeleteMixin, TimestampCreatedMixin, TimestampMixin
from app.models._tenant import TenantModel

if TYPE_CHECKING:
    from app.models.catalog import DocumentType, PropertyType, RelationType


# ── Condominium (root entity – NOT tenant-scoped) ────────────────────────


class Condominium(SoftDeleteMixin, Base):
    __tablename__ = "condominiums"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    department: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[Optional[str]] = mapped_column(String(100), server_default="Colombia")
    tax_id: Mapped[Optional[str]] = mapped_column(String(50))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    email: Mapped[Optional[str]] = mapped_column(String(150))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    timezone: Mapped[Optional[str]] = mapped_column(String(50), server_default="America/Bogota")
    currency: Mapped[Optional[str]] = mapped_column(String(10), server_default="COP")
    visitor_parking_hourly_rate: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0, server_default="0",
    )

    # relationships
    properties: Mapped[list["Property"]] = relationship(back_populates="condominium", lazy="selectin")
    user_roles: Mapped[list["UserCondominiumRole"]] = relationship(
        back_populates="condominium", lazy="selectin",
    )


# ── Role (global) ────────────────────────────────────────────────────────


class Role(TimestampCreatedMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))


# ── User (global – not tenant-scoped, can belong to many condos) ─────────


class User(SoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    phone_secondary: Mapped[Optional[str]] = mapped_column(String(30))
    document_type_id: Mapped[Optional[int]] = mapped_column(ForeignKey("document_types.id"))
    document_number: Mapped[Optional[str]] = mapped_column(String(50))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(150))
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(30))
    emergency_contact_relation: Mapped[Optional[str]] = mapped_column(String(50))
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # relationships
    document_type: Mapped[Optional["DocumentType"]] = relationship(lazy="joined")
    condominium_roles: Mapped[list["UserCondominiumRole"]] = relationship(
        back_populates="user", lazy="selectin",
    )
    properties_rel: Mapped[list["UserProperty"]] = relationship(
        back_populates="user", lazy="selectin",
    )
    devices: Mapped[list["UserDevice"]] = relationship(
        back_populates="user", lazy="selectin",
    )


# ── User ↔ Condominium ↔ Role ────────────────────────────────────────────


class UserCondominiumRole(Base):
    __tablename__ = "user_condominium_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    condominium_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("condominiums.id", ondelete="CASCADE"), nullable=False,
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "condominium_id", "role_id"),)

    user: Mapped["User"] = relationship(back_populates="condominium_roles")
    condominium: Mapped["Condominium"] = relationship(back_populates="user_roles")
    role: Mapped["Role"] = relationship(lazy="joined")


# ── Property (tenant-scoped) ─────────────────────────────────────────────


class Property(TenantModel, SoftDeleteMixin, Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number: Mapped[str] = mapped_column(String(20), nullable=False)
    block: Mapped[Optional[str]] = mapped_column(String(50))
    floor: Mapped[Optional[int]] = mapped_column(Integer)
    property_type_id: Mapped[int] = mapped_column(ForeignKey("property_types.id"), nullable=False)
    area_m2: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    aliquot: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    is_short_rent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("condominium_id", "number", "block"),)

    condominium: Mapped["Condominium"] = relationship(back_populates="properties")
    property_type: Mapped["PropertyType"] = relationship(lazy="joined")
    residents: Mapped[list["UserProperty"]] = relationship(back_populates="property", lazy="selectin")


# ── UserProperty (N:N user ↔ property) ───────────────────────────────────


class UserProperty(TimestampMixin, Base):
    __tablename__ = "user_properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False,
    )
    relation_type_id: Mapped[int] = mapped_column(ForeignKey("relation_types.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)

    __table_args__ = (UniqueConstraint("user_id", "property_id", "relation_type_id"),)

    user: Mapped["User"] = relationship(back_populates="properties_rel")
    property: Mapped["Property"] = relationship(back_populates="residents")
    relation_type: Mapped["RelationType"] = relationship(lazy="joined")


# ── UserDevice (FCM tokens) ──────────────────────────────────────────────


class UserDevice(TimestampMixin, Base):
    __tablename__ = "user_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    device_token: Mapped[str] = mapped_column(String(500), nullable=False)
    device_type: Mapped[str] = mapped_column(String(20), nullable=False)
    device_name: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "device_token"),)

    user: Mapped["User"] = relationship(back_populates="devices")
