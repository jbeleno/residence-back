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
    registered_by: UUID | None = None
    entry_time: datetime
    exit_time: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
