"""Tests for notifications module – service-level with mocked repository."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.notifications.service import NotificationService
from app.schemas.notification import NotificationCreate, NotificationMarkRead


# ── Helpers ───────────────────────────────────────────────────────────────


def _uid() -> uuid.UUID:
    return uuid.uuid4()


def _mock_notification(nid=None, is_read=False):
    n = MagicMock()
    n.id = nid or _uid()
    n.condominium_id = _uid()
    n.user_id = _uid()
    n.notification_type_id = 1
    n.notification_type = MagicMock(name="Pago")
    n.title = "Pago recibido"
    n.body = "Se registró un pago de $50,000"
    n.reference_type = "invoice"
    n.reference_id = _uid()
    n.is_read = is_read
    n.read_at = datetime(2025, 3, 1, tzinfo=timezone.utc) if is_read else None
    n.is_push_sent = False
    n.push_sent_at = None
    n.created_at = datetime(2025, 3, 1, tzinfo=timezone.utc)
    return n


def _repo() -> AsyncMock:
    return AsyncMock()


# ══════════════════════════════════════════════════════════════════════════
#  list_my_notifications
# ══════════════════════════════════════════════════════════════════════════


class TestListNotifications:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        cid, uid = _uid(), _uid()
        repo = _repo()
        repo.list_for_user.return_value = [_mock_notification(), _mock_notification()]

        svc = NotificationService(repo)
        result = await svc.list_my_notifications(cid, uid, False, 0, 30)
        assert len(result) == 2
        assert all("title" in r for r in result)

    @pytest.mark.asyncio
    async def test_empty(self):
        repo = _repo()
        repo.list_for_user.return_value = []
        svc = NotificationService(repo)
        result = await svc.list_my_notifications(_uid(), _uid(), False, 0, 30)
        assert result == []


# ══════════════════════════════════════════════════════════════════════════
#  unread_count
# ══════════════════════════════════════════════════════════════════════════


class TestUnreadCount:
    @pytest.mark.asyncio
    async def test_returns_count(self):
        cid, uid = _uid(), _uid()
        repo = _repo()
        repo.unread_count.return_value = 5

        svc = NotificationService(repo)
        result = await svc.unread_count(cid, uid)
        assert result == {"unread_count": 5}

    @pytest.mark.asyncio
    async def test_zero(self):
        repo = _repo()
        repo.unread_count.return_value = 0
        svc = NotificationService(repo)
        result = await svc.unread_count(_uid(), _uid())
        assert result["unread_count"] == 0


# ══════════════════════════════════════════════════════════════════════════
#  mark_read / mark_all_read
# ══════════════════════════════════════════════════════════════════════════


class TestMarkRead:
    @pytest.mark.asyncio
    async def test_mark_read(self):
        uid = _uid()
        repo = _repo()
        repo.mark_read.return_value = 2

        body = NotificationMarkRead(notification_ids=[_uid(), _uid()])
        svc = NotificationService(repo)
        result = await svc.mark_read(body, uid)
        assert "2" in result["message"]

    @pytest.mark.asyncio
    async def test_mark_all_read(self):
        cid, uid = _uid(), _uid()
        repo = _repo()
        repo.mark_all_read.return_value = 3

        svc = NotificationService(repo)
        result = await svc.mark_all_read(cid, uid)
        assert "3" in result["message"]


# ══════════════════════════════════════════════════════════════════════════
#  send_notification
# ══════════════════════════════════════════════════════════════════════════


class TestSendNotification:
    @pytest.mark.asyncio
    async def test_success(self):
        cid = _uid()
        repo = _repo()
        created = _mock_notification()
        repo.create.return_value = created

        body = NotificationCreate(
            user_id=_uid(),
            notification_type_id=1,
            title="Nueva noticia",
            body="Se publicó una nueva noticia",
        )
        svc = NotificationService(repo)
        result = await svc.send_notification(body, cid)
        assert result["title"] == "Pago recibido"
        repo.create.assert_awaited_once()


# ══════════════════════════════════════════════════════════════════════════
#  list_all
# ══════════════════════════════════════════════════════════════════════════


class TestListAll:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        cid, uid = _uid(), _uid()
        repo = _repo()
        repo.list_all.return_value = [_mock_notification(), _mock_notification()]

        svc = NotificationService(repo)
        result = await svc.list_all(cid, uid, 0, 50)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_empty(self):
        repo = _repo()
        repo.list_all.return_value = []
        svc = NotificationService(repo)
        result = await svc.list_all(_uid(), _uid(), 0, 50)
        assert result == []
