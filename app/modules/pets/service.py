"""Pet service."""

from __future__ import annotations

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.pets.repository import PetRepository
from app.schemas.pet import PetCreate, PetOut, PetUpdate


class PetService:
    def __init__(self, repo: PetRepository) -> None:
        self._repo = repo

    async def list_pets(self, cid: UUID, property_id, offset, limit):
        pets = await self._repo.list_pets(cid, property_id=property_id, offset=offset, limit=limit)
        return [self._out(p) for p in pets]

    async def get_pet(self, pet_id: int, cid: UUID):
        pet = await self._repo.get_by_id(pet_id, cid)
        if not pet:
            raise NotFoundError("Mascota no encontrada")
        return self._out(pet)

    async def create_pet(self, body: PetCreate, cid: UUID):
        prop = await self._repo.get_property(body.property_id, cid)
        if not prop:
            raise NotFoundError("Propiedad no encontrada en este condominio")
        pet = await self._repo.create(body.model_dump())
        return self._out(pet)

    async def update_pet(self, pet_id: int, body: PetUpdate, cid: UUID):
        pet = await self._repo.get_by_id(pet_id, cid)
        if not pet:
            raise NotFoundError("Mascota no encontrada")
        pet = await self._repo.update(pet, body.model_dump(exclude_unset=True))
        return self._out(pet)

    @staticmethod
    def _out(p) -> dict:
        out = PetOut.model_validate(p).model_dump()
        out["pet_species_name"] = p.pet_species.name if p.pet_species else None
        return out
