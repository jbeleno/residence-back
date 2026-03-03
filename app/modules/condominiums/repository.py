"""Condominium repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Condominium


class CondominiumRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_all(self, *, offset: int = 0, limit: int = 50) -> list[Condominium]:
        stmt = (
            select(Condominium)
            .where(Condominium.deleted_at.is_(None))
            .offset(offset)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        from sqlalchemy import func
        stmt = select(func.count(Condominium.id)).where(Condominium.deleted_at.is_(None))
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, cid: UUID) -> Condominium | None:
        result = await self._db.execute(
            select(Condominium).where(Condominium.id == cid, Condominium.deleted_at.is_(None))
        )
        return result.scalars().first()

    async def create(self, data: dict) -> Condominium:
        condo = Condominium(**data)
        self._db.add(condo)
        await self._db.commit()
        await self._db.refresh(condo)
        return condo

    async def update(self, condo: Condominium, data: dict) -> Condominium:
        for key, val in data.items():
            setattr(condo, key, val)
        await self._db.commit()
        await self._db.refresh(condo)
        return condo

    async def soft_delete(self, condo: Condominium) -> None:
        from datetime import datetime
        condo.deleted_at = datetime.utcnow()
        await self._db.commit()
