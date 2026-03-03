"""Tests for visitors module – service-level with mocked repository."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.visitors.service import VisitorService
from app.schemas.visitor import VisitorLogCreate


# ── Helpers ───────────────────────────────────────────────────────────────


def _uid() -> uuid.UUID:
    return uuid.uuid4()


def _mock_visitor(vid=None, has_exit=False):
    v = MagicMock()
    v.id = vid or _uid()
    v.condominium_id = _uid()
    v.property_id = _uid()
    v.visitor_name = "Juan Pérez"
    v.document_type_id = 1
    dt_mock = MagicMock()
    dt_mock.name = "Cédula"
    v.document_type = dt_mock
    v.document_number = "123456"
    v.is_guest = False
    v.vehicle_plate = "ABC123"
    v.authorized_by = _uid()
    v.authorized_user = MagicMock(full_name="Admin User")
    v.registered_by = _uid()
    v.entry_time = datetime(2025, 3, 1, 10, 0, tzinfo=timezone.utc)
    v.exit_time = datetime(2025, 3, 1, 15, 0, tzinfo=timezone.utc) if has_exit else None
    v.notes = None
    v.created_at = datetime(2025, 3, 1, 10, 0, tzinfo=timezone.utc)
    v.property = MagicMock(number="101")
    return v


def _repo() -> AsyncMock:
    return AsyncMock()


# ══════════════════════════════════════════════════════════════════════════
#  list_visitors / list_active
# ══════════════════════════════════════════════════════════════════════════


class TestListVisitors:
    @pytest.mark.asyncio
    async def test_list_visitors(self):
        cid = _uid()
        repo = _repo()
        repo.list_visitors.return_value = [_mock_visitor(), _mock_visitor()]

        svc = VisitorService(repo)
        result = await svc.list_visitors(cid, False, None, 0, 50)
        assert len(result) == 2
        assert all("visitor_name" in r for r in result)

    @pytest.mark.asyncio
    async def test_list_active(self):
        cid = _uid()
        repo = _repo()
        repo.list_visitors.return_value = [_mock_visitor()]

        svc = VisitorService(repo)
        result = await svc.list_active(cid)
        assert len(result) == 1
        repo.list_visitors.assert_awaited_once_with(cid, active_only=True)

    @pytest.mark.asyncio
    async def test_list_empty(self):
        repo = _repo()
        repo.list_visitors.return_value = []
        svc = VisitorService(repo)
        result = await svc.list_visitors(_uid(), False, None, 0, 50)
        assert result == []


# ══════════════════════════════════════════════════════════════════════════
#  get_visitor
# ══════════════════════════════════════════════════════════════════════════


class TestGetVisitor:
    @pytest.mark.asyncio
    async def test_found(self):
        vid, cid = _uid(), _uid()
        repo = _repo()
        repo.get_by_id.return_value = _mock_visitor(vid=vid)

        svc = VisitorService(repo)
        result = await svc.get_visitor(vid, cid)
        assert result["id"] == vid

    @pytest.mark.asyncio
    async def test_not_found(self):
        repo = _repo()
        repo.get_by_id.return_value = None
        svc = VisitorService(repo)
        with pytest.raises(NotFoundError):
            await svc.get_visitor(_uid(), _uid())


# ══════════════════════════════════════════════════════════════════════════
#  register_entry
# ══════════════════════════════════════════════════════════════════════════


class TestRegisterEntry:
    @pytest.mark.asyncio
    async def test_success(self):
        cid, uid = _uid(), _uid()
        repo = _repo()
        created = _mock_visitor()
        repo.create.return_value = created

        body = VisitorLogCreate(property_id=_uid(), visitor_name="Maria")
        svc = VisitorService(repo)
        result = await svc.register_entry(body, cid, uid)
        assert "visitor_name" in result
        repo.create.assert_awaited_once()


# ══════════════════════════════════════════════════════════════════════════
#  register_exit
# ══════════════════════════════════════════════════════════════════════════


class TestRegisterExit:
    @pytest.mark.asyncio
    async def test_success(self):
        vid, cid = _uid(), _uid()
        visitor = _mock_visitor(vid=vid, has_exit=False)
        repo = _repo()
        repo.get_by_id.return_value = visitor

        svc = VisitorService(repo)
        result = await svc.register_exit(vid, cid)

        assert visitor.exit_time is not None
        repo.commit.assert_awaited_once()
        repo.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_not_found(self):
        repo = _repo()
        repo.get_by_id.return_value = None
        svc = VisitorService(repo)
        with pytest.raises(NotFoundError):
            await svc.register_exit(_uid(), _uid())

    @pytest.mark.asyncio
    async def test_already_exited(self):
        visitor = _mock_visitor(has_exit=True)
        repo = _repo()
        repo.get_by_id.return_value = visitor

        svc = VisitorService(repo)
        with pytest.raises(BadRequestError, match="ya registró salida"):
            await svc.register_exit(visitor.id, _uid())
