"""Catalog schemas."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class CatalogBase(BaseModel):
    code: str
    name: str
    is_active: bool = True


class CatalogCreate(CatalogBase):
    pass


class CatalogUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    is_active: bool | None = None


class CatalogOut(CatalogBase):
    id: int

    model_config = {"from_attributes": True}


# Extended catalogs

class PriorityCreate(CatalogCreate):
    level: int = 0


class PriorityOut(CatalogOut):
    level: int = 0


class NotificationTypeCreate(CatalogCreate):
    template: str | None = None


class NotificationTypeOut(CatalogOut):
    template: str | None = None
