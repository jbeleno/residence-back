"""Condominium repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Condominium, Property


class CondominiumRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_featured(
        self, *, limit: int = 10, city: str | None = None,
    ) -> list[dict]:
        """List active condominiums with property/tower counts."""
        stmt = (
            select(
                Condominium.id,
                Condominium.name,
                Condominium.address,
                Condominium.city,
                Condominium.department,
                Condominium.logo_url,
                func.count(Property.id).label("total_properties"),
                func.count(func.distinct(Property.block)).label("total_towers"),
            )
            .outerjoin(
                Property,
                (Property.condominium_id == Condominium.id)
                & (Property.deleted_at.is_(None))
                & (Property.is_active.is_(True)),
            )
            .where(Condominium.deleted_at.is_(None))
            .group_by(Condominium.id)
            .order_by(Condominium.name)
            .limit(limit)
        )
        if city:
            stmt = stmt.where(Condominium.city.ilike(f"%{city}%"))
        result = await self._db.execute(stmt)
        return [row._asdict() for row in result.all()]

    async def count_featured(self, *, city: str | None = None) -> int:
        stmt = select(func.count(Condominium.id)).where(Condominium.deleted_at.is_(None))
        if city:
            stmt = stmt.where(Condominium.city.ilike(f"%{city}%"))
        result = await self._db.execute(stmt)
        return result.scalar_one()

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
