"""Tests for condominiums module (representative CRUD pattern)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.modules.condominiums.service import CondominiumService
from app.schemas.condominium import CondominiumCreate, CondominiumUpdate


def _mock_condo(name="Condo A", cid=None):
    c = MagicMock()
    c.id = cid or uuid.uuid4()
    c.name = name
    c.address = "Calle 1"
    c.city = "Bogotá"
    c.department = "Cundinamarca"
    c.country = "Colombia"
    c.tax_id = None
    c.phone = "300111"
    c.email = "c@c.com"
    c.logo_url = None
    c.timezone = "America/Bogota"
    c.currency = "COP"
    c.visitor_parking_hourly_rate = 5000
    c.created_at = None
    c.deleted_at = None
    return c


def _mock_repo() -> AsyncMock:
    return AsyncMock()


class TestCondominiumService:
    @pytest.mark.asyncio
    async def test_list_condominiums(self):
        c1, c2 = _mock_condo("A"), _mock_condo("B")
        repo = _mock_repo()
        repo.count = AsyncMock(return_value=2)
        repo.list_all = AsyncMock(return_value=[c1, c2])

        svc = CondominiumService(repo)
        items, total = await svc.list_condominiums(0, 50)

        assert total == 2
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_get_current_success(self):
        c = _mock_condo()
        repo = _mock_repo()
        repo.get_by_id = AsyncMock(return_value=c)

        svc = CondominiumService(repo)
        result = await svc.get_current(c.id)

        assert result.name == c.name

    @pytest.mark.asyncio
    async def test_get_current_not_found(self):
        repo = _mock_repo()
        repo.get_by_id = AsyncMock(return_value=None)

        svc = CondominiumService(repo)
        with pytest.raises(NotFoundError, match="no encontrado"):
            await svc.get_current(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_create(self):
        repo = _mock_repo()
        new_condo = _mock_condo("Nuevo")
        repo.create = AsyncMock(return_value=new_condo)

        svc = CondominiumService(repo)
        body = CondominiumCreate(name="Nuevo", address="Dir")
        result = await svc.create(body)

        assert result.name == "Nuevo"
        repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_success(self):
        c = _mock_condo()
        repo = _mock_repo()
        repo.get_by_id = AsyncMock(return_value=c)
        repo.update = AsyncMock(return_value=c)

        svc = CondominiumService(repo)
        body = CondominiumUpdate(name="Updated")
        result = await svc.update(c.id, body)

        repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        repo = _mock_repo()
        repo.get_by_id = AsyncMock(return_value=None)

        svc = CondominiumService(repo)
        body = CondominiumUpdate(name="X")
        with pytest.raises(NotFoundError):
            await svc.update(uuid.uuid4(), body)

    @pytest.mark.asyncio
    async def test_soft_delete_success(self):
        c = _mock_condo()
        repo = _mock_repo()
        repo.get_by_id = AsyncMock(return_value=c)
        repo.soft_delete = AsyncMock()

        svc = CondominiumService(repo)
        await svc.soft_delete(c.id)

        repo.soft_delete.assert_called_once_with(c)

    @pytest.mark.asyncio
    async def test_soft_delete_not_found(self):
        repo = _mock_repo()
        repo.get_by_id = AsyncMock(return_value=None)

        svc = CondominiumService(repo)
        with pytest.raises(NotFoundError):
            await svc.soft_delete(uuid.uuid4())
