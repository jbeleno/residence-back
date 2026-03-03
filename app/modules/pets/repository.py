"""Pet repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.core import Property
from app.models.pet import Pet


class PetRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_pets(
        self, cid: UUID, *, property_id: UUID | None = None, offset: int = 0, limit: int = 50
    ) -> list[Pet]:
        stmt = (
            select(Pet)
            .join(Property, Pet.property_id == Property.id)
            .options(selectinload(Pet.pet_species))
            .where(Property.condominium_id == cid, Pet.is_active.is_(True))
        )
        if property_id:
            stmt = stmt.where(Pet.property_id == property_id)
        stmt = stmt.order_by(Pet.name).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, pet_id: int, cid: UUID) -> Pet | None:
        result = await self._db.execute(
            select(Pet)
            .join(Property, Pet.property_id == Property.id)
            .options(selectinload(Pet.pet_species))
            .where(Pet.id == pet_id, Property.condominium_id == cid)
        )
        return result.scalars().first()

    async def get_property(self, property_id: UUID, cid: UUID) -> Property | None:
        result = await self._db.execute(
            select(Property).where(Property.id == property_id, Property.condominium_id == cid)
        )
        return result.scalars().first()

    async def create(self, data: dict) -> Pet:
        pet = Pet(**data)
        self._db.add(pet)
        await self._db.commit()
        await self._db.refresh(pet)
        return pet

    async def update(self, pet: Pet, data: dict) -> Pet:
        for k, v in data.items():
            setattr(pet, k, v)
        await self._db.commit()
        await self._db.refresh(pet)
        return pet
