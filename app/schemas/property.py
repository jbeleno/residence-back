"""Property schemas."""

from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import date, datetime

from pydantic import BaseModel


class PropertyCreate(BaseModel):
    number: str
    block: str | None = None
    floor: int | None = None
    property_type_id: int
    area_m2: float | None = None
    aliquot: float | None = None
    is_short_rent: bool = False


class PropertyUpdate(BaseModel):
    number: str | None = None
    block: str | None = None
    floor: int | None = None
    property_type_id: int | None = None
    area_m2: float | None = None
    aliquot: float | None = None
    is_short_rent: bool | None = None
    is_active: bool | None = None


class PropertyOut(BaseModel):
    id: UUID
    condominium_id: UUID
    number: str
    block: str | None = None
    floor: int | None = None
    property_type_id: int
    area_m2: float | None = None
    aliquot: float | None = None
    is_short_rent: bool = False
    is_active: bool = True
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserPropertyCreate(BaseModel):
    user_id: UUID
    property_id: UUID
    relation_type_id: int
    start_date: date | None = None
    end_date: date | None = None


class UserPropertyUpdate(BaseModel):
    is_active: bool | None = None
    start_date: date | None = None
    end_date: date | None = None


class UserPropertyTransfer(BaseModel):
    new_property_id: UUID
    relation_type_id: int | None = None
    start_date: date | None = None


class UserPropertyOut(BaseModel):
    id: int
    user_id: UUID
    property_id: UUID
    relation_type_id: int
    is_active: bool = True
    start_date: date | None = None
    end_date: date | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
