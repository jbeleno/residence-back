"""Audit logs router."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    get_current_condominium_id,
    get_current_role,
    require_admin,
)
from app.core.responses import success, success_list, PaginationMeta
from app.modules.audit_logs.repository import AuditLogRepository
from app.modules.audit_logs.service import AuditLogService

router = APIRouter(prefix="/audit-logs", tags=["Auditoría"])


def _service(db: AsyncSession = Depends(get_db)) -> AuditLogService:
    return AuditLogService(AuditLogRepository(db))


def _scope_condo(role: str, cid: UUID) -> UUID | None:
    """super_admin sees all condos; admin only their own."""
    return None if role == "super_admin" else cid


@router.get("/", dependencies=[Depends(require_admin)])
async def list_audit_logs(
    role: str = Depends(get_current_role),
    cid: UUID = Depends(get_current_condominium_id),
    user_id: UUID | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    svc: AuditLogService = Depends(_service),
):
    """List audit log entries.

    - super_admin: sees logs from all condominiums.
    - admin: sees only logs of the active condominium.
    """
    items, total = await svc.list_logs(
        condominium_id=_scope_condo(role, cid),
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        date_from=date_from,
        date_to=date_to,
        offset=skip,
        limit=limit,
    )
    return success_list(
        items, total=total,
        page=(skip // limit) + 1 if limit else 1,
        page_size=limit,
    )


@router.get("/{log_id}", dependencies=[Depends(require_admin)])
async def get_audit_log(
    log_id: int,
    role: str = Depends(get_current_role),
    cid: UUID = Depends(get_current_condominium_id),
    svc: AuditLogService = Depends(_service),
):
    return success(await svc.get_log(log_id, condominium_id=_scope_condo(role, cid)))
