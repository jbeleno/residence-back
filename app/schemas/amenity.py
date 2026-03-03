"""Amenity & Booking schemas."""

from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import datetime, time

from pydantic import BaseModel


class AmenityCreate(BaseModel):
    name: str
    description: str | None = None
    capacity: int | None = None
    hourly_cost: float = 0
    requires_approval: bool = False
    min_hours: int = 1
    max_hours: int = 8
    available_from: time | None = None
    available_until: time | None = None


class AmenityUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    capacity: int | None = None
    hourly_cost: float | None = None
    requires_approval: bool | None = None
    min_hours: int | None = None
    max_hours: int | None = None
    available_from: time | None = None
    available_until: time | None = None
    is_active: bool | None = None


class AmenityOut(BaseModel):
    id: int
    condominium_id: UUID
    name: str
    description: str | None = None
    capacity: int | None = None
    hourly_cost: float = 0
    requires_approval: bool = False
    min_hours: int = 1
    max_hours: int = 8
    available_from: time | None = None
    available_until: time | None = None
    is_active: bool = True
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class BookingCreate(BaseModel):
    amenity_id: int
    property_id: UUID
    start_time: datetime
    end_time: datetime
    notes: str | None = None


class BookingUpdateStatus(BaseModel):
    status_code: str  # e.g. "aprobada", "rechazada", "cancelada"


class BookingOut(BaseModel):
    id: UUID
    amenity_id: int
    amenity_name: str | None = None
    property_id: UUID
    booked_by: UUID
    booked_by_name: str | None = None
    booking_status_id: int
    booking_status_name: str | None = None
    start_time: datetime
    end_time: datetime
    total_cost: float = 0
    invoice_id: UUID | None = None
    notes: str | None = None
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
