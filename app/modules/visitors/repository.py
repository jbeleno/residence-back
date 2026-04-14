"""Visitor repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.core import Condominium, Property, UserProperty
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
            stmt = stmt.where(
                VisitorLog.entry_time.is_not(None),
                VisitorLog.exit_time.is_(None),
            )
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

    async def list_pending(self, cid: UUID) -> list[VisitorLog]:
        """List pre-registered visitors (entry_time is NULL)."""
        stmt = (
            select(VisitorLog)
            .options(
                selectinload(VisitorLog.property),
                selectinload(VisitorLog.document_type),
                selectinload(VisitorLog.authorized_user),
            )
            .where(
                VisitorLog.condominium_id == cid,
                VisitorLog.entry_time.is_(None),
            )
            .order_by(VisitorLog.created_at.desc())
            .limit(50)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_property_ids_in_condo(self, user_id: UUID, cid: UUID) -> set[UUID]:
        """Get all property IDs that belong to a user in a specific condominium."""
        stmt = (
            select(UserProperty.property_id)
            .join(Property, UserProperty.property_id == Property.id)
            .where(UserProperty.user_id == user_id, Property.condominium_id == cid)
        )
        result = await self._db.execute(stmt)
        return set(result.scalars().all())

    async def get_condominium(self, cid: UUID) -> Condominium | None:
        result = await self._db.execute(
            select(Condominium).where(Condominium.id == cid, Condominium.deleted_at.is_(None))
        )
        return result.scalars().first()

    async def get_property_by_number(self, cid: UUID, number: str) -> Property | None:
        result = await self._db.execute(
            select(Property).where(
                Property.condominium_id == cid,
                Property.number == number,
                Property.deleted_at.is_(None),
                Property.is_active.is_(True),
            )
        )
        return result.scalars().first()

    async def commit(self) -> None:
        await self._db.commit()

    async def refresh(self, obj) -> None:
        await self._db.refresh(obj)
