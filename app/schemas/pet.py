"""Pet schemas."""

from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class PetCreate(BaseModel):
    property_id: UUID
    name: str
    pet_species_id: int
    breed: str | None = None
    color: str | None = None
    weight_kg: float | None = None
    vaccination_up_to_date: bool = False
    photo_url: str | None = None
    notes: str | None = None


class PetUpdate(BaseModel):
    name: str | None = None
    breed: str | None = None
    color: str | None = None
    weight_kg: float | None = None
    vaccination_up_to_date: bool | None = None
    photo_url: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class PetOut(BaseModel):
    id: int
    property_id: UUID
    name: str
    pet_species_id: int
    species_name: str | None = None
    breed: str | None = None
    color: str | None = None
    weight_kg: float | None = None
    vaccination_up_to_date: bool = False
    photo_url: str | None = None
    notes: str | None = None
    is_active: bool = True
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
