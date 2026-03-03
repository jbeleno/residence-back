"""Condominium service."""

from __future__ import annotations

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.condominiums.repository import CondominiumRepository
from app.schemas.condominium import CondominiumCreate, CondominiumUpdate


class CondominiumService:
    def __init__(self, repo: CondominiumRepository) -> None:
        self._repo = repo

    async def list_condominiums(self, offset: int, limit: int):
        total = await self._repo.count()
        items = await self._repo.list_all(offset=offset, limit=limit)
        return items, total

    async def get_current(self, cid: UUID):
        condo = await self._repo.get_by_id(cid)
        if not condo:
            raise NotFoundError("Condominio no encontrado")
        return condo

    async def create(self, body: CondominiumCreate):
        return await self._repo.create(body.model_dump())

    async def update(self, cid: UUID, body: CondominiumUpdate):
        condo = await self._repo.get_by_id(cid)
        if not condo:
            raise NotFoundError("Condominio no encontrado")
        return await self._repo.update(condo, body.model_dump(exclude_unset=True))

    async def soft_delete(self, cid: UUID):
        condo = await self._repo.get_by_id(cid)
        if not condo:
            raise NotFoundError("Condominio no encontrado")
        await self._repo.soft_delete(condo)
