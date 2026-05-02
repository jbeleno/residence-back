"""Audit logs service."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.audit_log import AuditLog
from app.modules.audit_logs.repository import AuditLogRepository
from app.schemas.audit_log import AuditLogOut


class AuditLogService:
    def __init__(self, repo: AuditLogRepository) -> None:
        self._repo = repo

    async def list_logs(
        self,
        *,
        condominium_id: UUID | None,
        user_id: UUID | None,
        action: str | None,
        entity_type: str | None,
        entity_id: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
        offset: int,
        limit: int,
    ) -> tuple[list[dict], int]:
        items = await self._repo.list_logs(
            condominium_id=condominium_id, user_id=user_id, action=action,
            entity_type=entity_type, entity_id=entity_id,
            date_from=date_from, date_to=date_to,
            offset=offset, limit=limit,
        )
        total = await self._repo.count_logs(
            condominium_id=condominium_id, user_id=user_id, action=action,
            entity_type=entity_type, entity_id=entity_id,
            date_from=date_from, date_to=date_to,
        )
        return [self._out(x) for x in items], total

    async def get_log(self, log_id: int, *, condominium_id: UUID | None) -> dict:
        log = await self._repo.get_by_id(log_id)
        if not log:
            raise NotFoundError("Audit log no encontrado")
        # Admin (non-super) can only see their own condo's logs.
        if condominium_id is not None and log.condominium_id != condominium_id:
            raise NotFoundError("Audit log no encontrado")
        return self._out(log)

    @staticmethod
    def _out(log: AuditLog) -> dict:
        return AuditLogOut(
            id=log.id,
            user_id=log.user_id,
            user_email=log.user_email,
            user_role=log.user_role,
            condominium_id=log.condominium_id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            changes=log.changes,
            metadata=log.extra_metadata,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            method=log.method,
            path=log.path,
            status_code=log.status_code,
            created_at=log.created_at,
        ).model_dump()
