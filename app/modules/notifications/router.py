"""Notification router."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    get_current_condominium_id,
    get_current_user,
    require_admin,
)
from app.core.responses import success
from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.service import NotificationService
from app.schemas.notification import NotificationCreate, NotificationMarkRead

router = APIRouter(prefix="/notifications", tags=["Notificaciones"])


def _service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(NotificationRepository(db))


# ── My notifications ──────────────────────────────────────────────────────


@router.get("/me")
async def list_my_notifications(
    cid: UUID = Depends(get_current_condominium_id),
    current_user=Depends(get_current_user),
    unread_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    svc: NotificationService = Depends(_service),
):
    return success(await svc.list_my_notifications(cid, current_user.id, unread_only, skip, limit))


@router.get("/me/unread-count")
async def unread_count(
    cid: UUID = Depends(get_current_condominium_id),
    current_user=Depends(get_current_user),
    svc: NotificationService = Depends(_service),
):
    return success(await svc.unread_count(cid, current_user.id))


@router.post("/me/mark-read")
async def mark_notifications_read(
    body: NotificationMarkRead,
    current_user=Depends(get_current_user),
    svc: NotificationService = Depends(_service),
):
    return success(await svc.mark_read(body, current_user.id))


@router.post("/me/mark-all-read")
async def mark_all_read(
    cid: UUID = Depends(get_current_condominium_id),
    current_user=Depends(get_current_user),
    svc: NotificationService = Depends(_service),
):
    return success(await svc.mark_all_read(cid, current_user.id))


# ── Admin ─────────────────────────────────────────────────────────────────


@router.post("/send", dependencies=[Depends(require_admin)], status_code=201)
async def send_notification(
    body: NotificationCreate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: NotificationService = Depends(_service),
):
    return success(await svc.send_notification(body, cid))


@router.get("/", dependencies=[Depends(require_admin)])
async def list_all_notifications(
    cid: UUID = Depends(get_current_condominium_id),
    user_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    svc: NotificationService = Depends(_service),
):
    return success(await svc.list_all(cid, user_id, skip, limit))
