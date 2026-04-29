"""Tests for users module – service-level with mocked repository."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.modules.users.service import UserService
from app.schemas.user import UserCreate, UserDeviceCreate, UserUpdate


# ── Helpers ───────────────────────────────────────────────────────────────


def _uid() -> uuid.UUID:
    return uuid.uuid4()


def _mock_user(uid=None, email="test@test.com"):
    u = MagicMock()
    u.id = uid or _uid()
    u.email = email
    u.full_name = "Test User"
    u.phone = None
    u.is_active = True
    u.email_verified = False
    u.deleted_at = None
    return u


def _mock_device(did=1, token="tok123"):
    d = MagicMock()
    d.id = did
    d.device_token = token
    d.device_type = "android"
    d.device_name = "Pixel"
    d.is_active = True
    return d


def _mock_role(rid=1, name="admin"):
    r = MagicMock()
    r.id = rid
    r.role_name = name
    return r


def _repo() -> AsyncMock:
    return AsyncMock()


# ══════════════════════════════════════════════════════════════════════════
#  list_users
# ══════════════════════════════════════════════════════════════════════════


class TestListUsers:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        cid = _uid()
        repo = _repo()
        repo.list_by_condominium.return_value = [_mock_user(), _mock_user()]

        svc = UserService(repo)
        result = await svc.list_users(cid, 0, 50)

        assert len(result) == 2
        repo.list_by_condominium.assert_awaited_once_with(cid, offset=0, limit=50)

    @pytest.mark.asyncio
    async def test_empty_list(self):
        repo = _repo()
        repo.list_by_condominium.return_value = []
        svc = UserService(repo)
        result = await svc.list_users(_uid(), 0, 50)
        assert result == []


# ══════════════════════════════════════════════════════════════════════════
#  get_user
# ══════════════════════════════════════════════════════════════════════════


class TestGetUser:
    @pytest.mark.asyncio
    async def test_found(self):
        uid = _uid()
        user = _mock_user(uid=uid)
        repo = _repo()
        repo.get_by_id.return_value = user

        svc = UserService(repo)
        result = await svc.get_user(uid)
        assert result.id == uid

    @pytest.mark.asyncio
    async def test_not_found(self):
        repo = _repo()
        repo.get_by_id.return_value = None
        svc = UserService(repo)
        with pytest.raises(NotFoundError):
            await svc.get_user(_uid())


# ══════════════════════════════════════════════════════════════════════════
#  create_user
# ══════════════════════════════════════════════════════════════════════════


class TestCreateUser:
    @pytest.mark.asyncio
    async def test_success(self):
        cid = _uid()
        repo = _repo()
        repo.get_by_email.return_value = None

        created = _mock_user()
        repo.create_user.return_value = created

        body = MagicMock()
        body.model_dump.return_value = {"full_name": "X", "email": "x@x.com"}
        body.password = "secret"
        body.role_id = 2
        body.condominium_id = None
        body.email = "x@x.com"

        svc = UserService(repo)
        user, was_existing = await svc.create_user(body, cid)

        assert user == created
        assert was_existing is False
        repo.create_user.assert_awaited_once()
        repo.create_ucr.assert_awaited_once()
        repo.commit_and_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_existing_email_auto_links_to_new_condo(self):
        """If email exists and user has no role in target condo, auto-link them."""
        cid = _uid()
        existing = _mock_user(email="dup@dup.com")
        repo = _repo()
        repo.get_by_email.return_value = existing
        repo.get_ucr.return_value = None  # No existe UCR en este condo

        body = MagicMock()
        body.model_dump.return_value = {"full_name": "X", "email": "dup@dup.com"}
        body.password = "secret"
        body.role_id = 4
        body.condominium_id = None
        body.email = "dup@dup.com"

        svc = UserService(repo)
        user, was_existing = await svc.create_user(body, cid)

        assert user == existing
        assert was_existing is True
        repo.create_user.assert_not_awaited()  # No crea otro user
        repo.create_ucr.assert_awaited_once()  # Solo crea UCR

    @pytest.mark.asyncio
    async def test_existing_email_same_condo_fails(self):
        """If user already has a role in this condo, fail."""
        cid = _uid()
        existing = _mock_user()
        repo = _repo()
        repo.get_by_email.return_value = existing
        repo.get_ucr.return_value = MagicMock()  # Ya tiene UCR aquí

        body = MagicMock()
        body.model_dump.return_value = {"full_name": "X", "email": "dup@dup.com"}
        body.password = "secret"
        body.role_id = 4
        body.condominium_id = None
        body.email = "dup@dup.com"

        svc = UserService(repo)
        with pytest.raises(ConflictError, match="ya está asignado"):
            await svc.create_user(body, cid)

    @pytest.mark.asyncio
    async def test_default_role(self):
        """When no role_id is provided, default to residente (4)."""
        repo = _repo()
        repo.get_by_email.return_value = None
        created = _mock_user()
        repo.create_user.return_value = created

        body = MagicMock()
        body.model_dump.return_value = {"full_name": "X", "email": "x@x.com"}
        body.password = "secret"
        body.role_id = None
        body.condominium_id = None
        body.email = "x@x.com"

        svc = UserService(repo)
        cid = _uid()
        user, was_existing = await svc.create_user(body, cid)
        assert user == created
        assert was_existing is False
        repo.create_ucr.assert_awaited_once()


# ══════════════════════════════════════════════════════════════════════════
#  update_user
# ══════════════════════════════════════════════════════════════════════════


class TestUpdateUser:
    @pytest.mark.asyncio
    async def test_success(self):
        uid = _uid()
        user = _mock_user(uid=uid)
        repo = _repo()
        repo.get_by_id.return_value = user
        repo.update.return_value = user

        body = UserUpdate(full_name="New Name")
        svc = UserService(repo)
        result = await svc.update_user(uid, body)
        assert result == user
        repo.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_not_found(self):
        repo = _repo()
        repo.get_by_id.return_value = None
        svc = UserService(repo)
        with pytest.raises(NotFoundError):
            await svc.update_user(_uid(), UserUpdate(full_name="X"))


# ══════════════════════════════════════════════════════════════════════════
#  Devices
# ══════════════════════════════════════════════════════════════════════════


class TestDevices:
    @pytest.mark.asyncio
    async def test_register_new_device(self):
        uid = _uid()
        repo = _repo()
        repo.get_device.return_value = None
        new_dev = _mock_device()
        repo.add_device.return_value = new_dev

        body = UserDeviceCreate(device_token="tok", device_type="ios")
        svc = UserService(repo)
        result = await svc.register_device(uid, body)
        assert result == new_dev
        repo.add_device.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_existing_device_reactivates(self):
        uid = _uid()
        existing = _mock_device()
        existing.is_active = False
        repo = _repo()
        repo.get_device.return_value = existing

        body = UserDeviceCreate(device_token="tok", device_type="android", device_name="Pixel")
        svc = UserService(repo)
        result = await svc.register_device(uid, body)

        assert result.is_active is True
        repo.commit_and_refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_devices(self):
        uid = _uid()
        repo = _repo()
        repo.list_devices.return_value = [_mock_device(), _mock_device(did=2)]

        svc = UserService(repo)
        result = await svc.list_devices(uid)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_deactivate_success(self):
        uid = _uid()
        dev = _mock_device()
        repo = _repo()
        repo.get_device_by_id.return_value = dev

        svc = UserService(repo)
        await svc.deactivate_device(1, uid)
        assert dev.is_active is False

    @pytest.mark.asyncio
    async def test_deactivate_not_found(self):
        repo = _repo()
        repo.get_device_by_id.return_value = None
        svc = UserService(repo)
        with pytest.raises(NotFoundError):
            await svc.deactivate_device(999, _uid())
