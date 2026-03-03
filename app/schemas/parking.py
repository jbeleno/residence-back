"""Parking schemas."""

from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class ParkingSpaceCreate(BaseModel):
    space_number: str
    parking_space_type_id: int
    property_id: UUID | None = None


class ParkingSpaceUpdate(BaseModel):
    space_number: str | None = None
    parking_space_type_id: int | None = None
    property_id: UUID | None = None
    is_active: bool | None = None


class ParkingSpaceOut(BaseModel):
    id: int
    condominium_id: UUID
    space_number: str
    parking_space_type_id: int
    parking_type_name: str | None = None
    property_id: UUID | None = None
    is_active: bool = True
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class VehicleCreate(BaseModel):
    property_id: UUID
    license_plate: str
    brand: str | None = None
    model: str | None = None
    color: str | None = None
    vehicle_type_id: int


class VehicleUpdate(BaseModel):
    brand: str | None = None
    model: str | None = None
    color: str | None = None
    vehicle_type_id: int | None = None
    is_active: bool | None = None


class VehicleOut(BaseModel):
    id: int
    condominium_id: UUID
    property_id: UUID
    license_plate: str
    brand: str | None = None
    model: str | None = None
    color: str | None = None
    vehicle_type_id: int
    vehicle_type_name: str | None = None
    is_active: bool = True
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class VisitorParkingCreate(BaseModel):
    visitor_log_id: UUID
    parking_space_id: int


class VisitorParkingExit(BaseModel):
    is_paid: bool = True


class VisitorParkingOut(BaseModel):
    id: int
    visitor_log_id: UUID
    parking_space_id: int
    entry_time: datetime
    exit_time: datetime | None = None
    hourly_rate: float = 0
    total_cost: float | None = None
    is_paid: bool = False
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
