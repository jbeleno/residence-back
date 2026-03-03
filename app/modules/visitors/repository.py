"""Visitor repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.visitor import VisitorLog


class VisitorRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_visitors(
        self,
        cid: UUID,
        *,
        active_only: bool = False,
        property_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[VisitorLog]:
        stmt = (
            select(VisitorLog)
            .options(
                selectinload(VisitorLog.property),
                selectinload(VisitorLog.document_type),
                selectinload(VisitorLog.authorized_user),
            )
            .where(VisitorLog.condominium_id == cid)
        )
        if active_only:
            stmt = stmt.where(VisitorLog.exit_time.is_(None))
        if property_id:
            stmt = stmt.where(VisitorLog.property_id == property_id)
        stmt = stmt.order_by(VisitorLog.entry_time.desc()).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, visitor_id: UUID, cid: UUID) -> VisitorLog | None:
        result = await self._db.execute(
            select(VisitorLog)
            .options(
                selectinload(VisitorLog.property),
                selectinload(VisitorLog.document_type),
                selectinload(VisitorLog.authorized_user),
            )
            .where(VisitorLog.id == visitor_id, VisitorLog.condominium_id == cid)
        )
        return result.scalars().first()

    async def create(self, visitor: VisitorLog) -> VisitorLog:
        self._db.add(visitor)
        await self._db.commit()
        await self._db.refresh(visitor)
        return visitor

    async def commit(self) -> None:
        await self._db.commit()

    async def refresh(self, obj) -> None:
        await self._db.refresh(obj)
