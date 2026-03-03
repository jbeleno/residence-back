"""Tests for properties module – service-level with mocked repository."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.modules.properties.service import PropertyService
from app.schemas.property import (
    PropertyCreate,
    PropertyUpdate,
    UserPropertyCreate,
    UserPropertyUpdate,
)


# ── Helpers ───────────────────────────────────────────────────────────────


def _uid() -> uuid.UUID:
    return uuid.uuid4()


def _mock_property(pid=None, number="101"):
    p = MagicMock()
    p.id = pid or _uid()
    p.condominium_id = _uid()
    p.number = number
    p.block = "A"
    p.floor = 1
    p.property_type_id = 1
    pt_mock = MagicMock()
    pt_mock.name = "Apartamento"
    p.property_type = pt_mock
    p.area_m2 = 60.0
    p.aliquot = 0.5
    p.is_short_rent = False
    p.is_active = True
    p.created_at = None
    p.deleted_at = None
    return p


def _mock_assignment(aid=1):
    up = MagicMock()
    up.id = aid
    up.user_id = _uid()
    up.property_id = _uid()
    up.relation_type_id = 1
    rt_mock = MagicMock()
    rt_mock.name = "Propietario"
    up.relation_type = rt_mock
    up.user = MagicMock(full_name="Resident A")
    up.is_active = True
    up.start_date = None
    up.end_date = None
    up.created_at = None
    return up


def _repo() -> AsyncMock:
    return AsyncMock()


# ══════════════════════════════════════════════════════════════════════════
#  list_properties
# ══════════════════════════════════════════════════════════════════════════


class TestListProperties:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        cid = _uid()
        repo = _repo()
        repo.list_by_condo.return_value = [_mock_property(number="101"), _mock_property(number="102")]

        svc = PropertyService(repo)
        result = await svc.list_properties(cid, None, 0, 50)

        assert len(result) == 2
        assert all("property_type_name" in r for r in result)

    @pytest.mark.asyncio
    async def test_empty(self):
        repo = _repo()
        repo.list_by_condo.return_value = []
        svc = PropertyService(repo)
        result = await svc.list_properties(_uid(), None, 0, 50)
        assert result == []


# ══════════════════════════════════════════════════════════════════════════
#  get_property
# ══════════════════════════════════════════════════════════════════════════


class TestGetProperty:
    @pytest.mark.asyncio
    async def test_found(self):
        pid, cid = _uid(), _uid()
        repo = _repo()
        repo.get_by_id.return_value = _mock_property(pid=pid)

        svc = PropertyService(repo)
        result = await svc.get_property(pid, cid)
        assert result["id"] == pid

    @pytest.mark.asyncio
    async def test_not_found(self):
        repo = _repo()
        repo.get_by_id.return_value = None
        svc = PropertyService(repo)
        with pytest.raises(NotFoundError):
            await svc.get_property(_uid(), _uid())


# ══════════════════════════════════════════════════════════════════════════
#  create_property
# ══════════════════════════════════════════════════════════════════════════


class TestCreateProperty:
    @pytest.mark.asyncio
    async def test_success(self):
        cid = _uid()
        repo = _repo()
        created = _mock_property()
        repo.create.return_value = created

        body = PropertyCreate(number="201", property_type_id=1)
        svc = PropertyService(repo)
        result = await svc.create_property(body, cid)
        assert "property_type_name" in result
        repo.create.assert_awaited_once()


# ══════════════════════════════════════════════════════════════════════════
#  update_property
# ══════════════════════════════════════════════════════════════════════════


class TestUpdateProperty:
    @pytest.mark.asyncio
    async def test_success(self):
        pid, cid = _uid(), _uid()
        prop = _mock_property(pid=pid)
        repo = _repo()
        repo.get_by_id.return_value = prop
        repo.update.return_value = prop

        body = PropertyUpdate(number="201B")
        svc = PropertyService(repo)
        result = await svc.update_property(pid, body, cid)
        assert result["id"] == pid

    @pytest.mark.asyncio
    async def test_not_found(self):
        repo = _repo()
        repo.get_by_id.return_value = None
        svc = PropertyService(repo)
        with pytest.raises(NotFoundError):
            await svc.update_property(_uid(), PropertyUpdate(number="X"), _uid())


# ══════════════════════════════════════════════════════════════════════════
#  Residents
# ══════════════════════════════════════════════════════════════════════════


class TestResidents:
    @pytest.mark.asyncio
    async def test_list_residents(self):
        pid, cid = _uid(), _uid()
        repo = _repo()
        repo.get_by_id.return_value = _mock_property(pid=pid)
        repo.list_residents.return_value = [_mock_assignment(), _mock_assignment(aid=2)]

        svc = PropertyService(repo)
        result = await svc.list_residents(pid, cid, True)
        assert len(result) == 2
        assert all("relation_type_name" in r for r in result)

    @pytest.mark.asyncio
    async def test_list_residents_property_not_found(self):
        repo = _repo()
        repo.get_by_id.return_value = None
        svc = PropertyService(repo)
        with pytest.raises(NotFoundError):
            await svc.list_residents(_uid(), _uid(), True)

    @pytest.mark.asyncio
    async def test_assign_resident(self):
        cid = _uid()
        pid = _uid()
        repo = _repo()
        repo.get_by_id.return_value = _mock_property(pid=pid)
        repo.create_assignment.return_value = _mock_assignment()

        body = UserPropertyCreate(user_id=_uid(), property_id=pid, relation_type_id=1)
        svc = PropertyService(repo)
        result = await svc.assign_resident(body, cid)
        assert "user_full_name" in result

    @pytest.mark.asyncio
    async def test_assign_resident_property_not_found(self):
        repo = _repo()
        repo.get_by_id.return_value = None
        svc = PropertyService(repo)
        body = UserPropertyCreate(user_id=_uid(), property_id=_uid(), relation_type_id=1)
        with pytest.raises(NotFoundError):
            await svc.assign_resident(body, _uid())

    @pytest.mark.asyncio
    async def test_update_assignment(self):
        repo = _repo()
        up = _mock_assignment()
        repo.get_assignment_by_id.return_value = up
        repo.update_assignment.return_value = up

        body = UserPropertyUpdate(is_active=False)
        svc = PropertyService(repo)
        result = await svc.update_assignment(1, body)
        assert "relation_type_name" in result

    @pytest.mark.asyncio
    async def test_update_assignment_not_found(self):
        repo = _repo()
        repo.get_assignment_by_id.return_value = None
        svc = PropertyService(repo)
        with pytest.raises(NotFoundError):
            await svc.update_assignment(999, UserPropertyUpdate(is_active=False))
