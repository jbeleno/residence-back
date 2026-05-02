"""Audit logs repository."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _base_filtered(
        self,
        *,
        condominium_id: UUID | None,
        user_id: UUID | None,
        action: str | None,
        entity_type: str | None,
        entity_id: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ):
        stmt = select(AuditLog)
        if condominium_id is not None:
            stmt = stmt.where(AuditLog.condominium_id == condominium_id)
        if user_id is not None:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(AuditLog.entity_id == str(entity_id))
        if date_from:
            stmt = stmt.where(AuditLog.created_at >= date_from)
        if date_to:
            stmt = stmt.where(AuditLog.created_at <= date_to)
        return stmt

    async def list_logs(
        self,
        *,
        condominium_id: UUID | None = None,
        user_id: UUID | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        stmt = (
            self._base_filtered(
                condominium_id=condominium_id, user_id=user_id, action=action,
                entity_type=entity_type, entity_id=entity_id,
                date_from=date_from, date_to=date_to,
            )
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count_logs(
        self,
        *,
        condominium_id: UUID | None = None,
        user_id: UUID | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        stmt = self._base_filtered(
            condominium_id=condominium_id, user_id=user_id, action=action,
            entity_type=entity_type, entity_id=entity_id,
            date_from=date_from, date_to=date_to,
        ).with_only_columns(func.count(AuditLog.id))
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, log_id: int) -> AuditLog | None:
        result = await self._db.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        return result.scalars().first()
