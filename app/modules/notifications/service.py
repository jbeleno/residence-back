"""Notification service."""

from __future__ import annotations

from uuid import UUID

from app.models.notification import Notification
from app.modules.notifications.repository import NotificationRepository
from app.schemas.notification import NotificationCreate, NotificationMarkRead, NotificationOut


class NotificationService:
    def __init__(self, repo: NotificationRepository) -> None:
        self._repo = repo

    async def list_my_notifications(self, cid, user_id, unread_only, offset, limit):
        items = await self._repo.list_for_user(cid, user_id, unread_only=unread_only, offset=offset, limit=limit)
        return [self._out(n) for n in items]

    async def unread_count(self, cid: UUID, user_id: UUID):
        count = await self._repo.unread_count(cid, user_id)
        return {"unread_count": count}

    async def mark_read(self, body: NotificationMarkRead, user_id: UUID):
        updated = await self._repo.mark_read(body.notification_ids, user_id)
        return {"message": f"{updated} notificación(es) marcada(s) como leída(s)"}

    async def mark_all_read(self, cid: UUID, user_id: UUID):
        updated = await self._repo.mark_all_read(cid, user_id)
        return {"message": f"{updated} notificación(es) marcada(s) como leída(s)"}

    async def send_notification(self, body: NotificationCreate, cid: UUID):
        notif = Notification(condominium_id=cid, **body.model_dump())
        notif = await self._repo.create(notif)
        return self._out(notif)

    async def list_all(self, cid, user_id, offset, limit):
        items = await self._repo.list_all(cid, user_id=user_id, offset=offset, limit=limit)
        return [self._out(n) for n in items]

    @staticmethod
    def _out(n: Notification) -> dict:
        return NotificationOut(
            id=n.id,
            condominium_id=n.condominium_id,
            user_id=n.user_id,
            notification_type_id=n.notification_type_id,
            notification_type_name=n.notification_type.name if n.notification_type else None,
            title=n.title,
            body=n.body,
            reference_type=n.reference_type,
            reference_id=n.reference_id,
            is_read=n.is_read,
            read_at=n.read_at,
            is_push_sent=n.is_push_sent,
            created_at=n.created_at,
        ).model_dump()
