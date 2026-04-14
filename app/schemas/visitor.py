"""Visitor schemas."""

from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class VisitorLogCreate(BaseModel):
    property_id: UUID
    visitor_name: str
    document_type_id: int | None = None
    document_number: str | None = None
    is_guest: bool = False
    vehicle_plate: str | None = None
    notes: str | None = None


class ResidentVisitorCreate(BaseModel):
    visitor_name: str
    document_number: str | None = None
    vehicle_plate: str | None = None
    notes: str | None = None


class VisitorLogExit(BaseModel):
    exit_time: datetime | None = None


class VisitorLogOut(BaseModel):
    id: UUID
    condominium_id: UUID
    property_id: UUID
    visitor_name: str
    document_type_id: int | None = None
    document_number: str | None = None
    is_guest: bool = False
    vehicle_plate: str | None = None
    authorized_by: UUID | None = None
    authorized_by_name: str | None = None
    registered_by: UUID | None = None
    entry_time: datetime | None = None
    exit_time: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None
    property_number: str | None = None
    document_type_name: str | None = None
    status: str | None = None

    model_config = {"from_attributes": True}
