"""Condominium schemas."""

from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class CondominiumCreate(BaseModel):
    name: str
    address: str | None = None
    city: str | None = None
    department: str | None = None
    country: str | None = "Colombia"
    tax_id: str | None = None
    phone: str | None = None
    email: str | None = None
    logo_url: str | None = None
    timezone: str | None = "America/Bogota"
    currency: str | None = "COP"
    visitor_parking_hourly_rate: float = 0


class CondominiumUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    department: str | None = None
    country: str | None = None
    tax_id: str | None = None
    phone: str | None = None
    email: str | None = None
    logo_url: str | None = None
    timezone: str | None = None
    currency: str | None = None
    visitor_parking_hourly_rate: float | None = None


class CondominiumOut(BaseModel):
    id: UUID
    name: str
    address: str | None = None
    city: str | None = None
    department: str | None = None
    country: str | None = None
    tax_id: str | None = None
    phone: str | None = None
    email: str | None = None
    logo_url: str | None = None
    timezone: str | None = None
    currency: str | None = None
    visitor_parking_hourly_rate: float = 0
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
