"""Notification repository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_for_user(
        self,
        cid: UUID,
        user_id: UUID,
        *,
        unread_only: bool = False,
        offset: int = 0,
        limit: int = 30,
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .options(selectinload(Notification.notification_type))
            .where(Notification.condominium_id == cid, Notification.user_id == user_id)
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def unread_count(self, cid: UUID, user_id: UUID) -> int:
        result = await self._db.execute(
            select(func.count(Notification.id)).where(
                Notification.condominium_id == cid,
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return result.scalar_one()

    async def mark_read(self, notification_ids: list, user_id: UUID) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            update(Notification)
            .where(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
            )
            .values(is_read=True, read_at=now)
        )
        result = await self._db.execute(stmt)
        await self._db.commit()
        return result.rowcount  # type: ignore[return-value]

    async def mark_all_read(self, cid: UUID, user_id: UUID) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            update(Notification)
            .where(
                Notification.condominium_id == cid,
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True, read_at=now)
        )
        result = await self._db.execute(stmt)
        await self._db.commit()
        return result.rowcount  # type: ignore[return-value]

    async def create(self, notif: Notification) -> Notification:
        self._db.add(notif)
        await self._db.commit()
        await self._db.refresh(notif)
        return notif

    async def list_all(
        self,
        cid: UUID,
        *,
        user_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .options(selectinload(Notification.notification_type))
            .where(Notification.condominium_id == cid)
        )
        if user_id:
            stmt = stmt.where(Notification.user_id == user_id)
        stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
