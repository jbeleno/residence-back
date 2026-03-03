"""Catalog repository – generic CRUD for all catalog tables."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import (
    BookingStatus, ChargeCategory, DocumentType, NotificationType,
    ParkingSpaceType, PaymentMethod, PaymentStatus, PetSpecies,
    PqrStatus, PqrType, Priority, PropertyType, RelationType, VehicleType,
)

CATALOG_MAP: dict[str, type] = {
    "document-types": DocumentType,
    "property-types": PropertyType,
    "relation-types": RelationType,
    "booking-statuses": BookingStatus,
    "payment-statuses": PaymentStatus,
    "payment-methods": PaymentMethod,
    "parking-space-types": ParkingSpaceType,
    "vehicle-types": VehicleType,
    "pet-species": PetSpecies,
    "charge-categories": ChargeCategory,
    "pqr-types": PqrType,
    "pqr-statuses": PqrStatus,
    "priorities": Priority,
    "notification-types": NotificationType,
}


class CatalogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @staticmethod
    def resolve_model(catalog_name: str):
        return CATALOG_MAP.get(catalog_name)

    async def list_all(self, model, *, active_only: bool = True):
        stmt = select(model)
        if active_only:
            stmt = stmt.where(model.is_active.is_(True))
        stmt = stmt.order_by(model.id)
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, model, item_id: int):
        result = await self._db.execute(select(model).where(model.id == item_id))
        return result.scalars().first()

    async def create(self, model, data: dict):
        item = model(**data)
        self._db.add(item)
        await self._db.commit()
        await self._db.refresh(item)
        return item

    async def update(self, item, data: dict):
        for key, val in data.items():
            setattr(item, key, val)
        await self._db.commit()
        await self._db.refresh(item)
        return item
