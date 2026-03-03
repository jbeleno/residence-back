"""Catalog (lookup) tables – id SERIAL, code, name, is_active.

These are **global** tables (not tenant-scoped).
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models._mixins import TimestampCreatedMixin


# ── Abstract base ─────────────────────────────────────────────────────────


class _CatalogBase(TimestampCreatedMixin):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


# ── Concrete tables ──────────────────────────────────────────────────────


class DocumentType(_CatalogBase, Base):
    __tablename__ = "document_types"


class PropertyType(_CatalogBase, Base):
    __tablename__ = "property_types"


class RelationType(_CatalogBase, Base):
    __tablename__ = "relation_types"


class BookingStatus(_CatalogBase, Base):
    __tablename__ = "booking_statuses"


class PaymentStatus(_CatalogBase, Base):
    __tablename__ = "payment_statuses"


class PaymentMethod(_CatalogBase, Base):
    __tablename__ = "payment_methods"


class ParkingSpaceType(_CatalogBase, Base):
    __tablename__ = "parking_space_types"


class VehicleType(_CatalogBase, Base):
    __tablename__ = "vehicle_types"


class PetSpecies(_CatalogBase, Base):
    __tablename__ = "pet_species"


class ChargeCategory(_CatalogBase, Base):
    __tablename__ = "charge_categories"


class PqrType(_CatalogBase, Base):
    __tablename__ = "pqr_types"


class PqrStatus(_CatalogBase, Base):
    __tablename__ = "pqr_statuses"


class Priority(_CatalogBase, Base):
    __tablename__ = "priorities"
    level: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class NotificationType(_CatalogBase, Base):
    __tablename__ = "notification_types"
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
