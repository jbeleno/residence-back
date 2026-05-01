"""Tests for the auth module: service + repository logic."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import BadRequestError, ForbiddenError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.modules.auth.service import AuthService
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RequestPasswordResetRequest,
    RequestPinRequest,
    ResetPasswordRequest,
    SelectCondominiumRequest,
    VerifyEmailRequest,
    VerifyLoginPinRequest,
)


# ── Helper factories ──────────────────────────────────────────────────────


def _mock_user(
    *,
    uid: uuid.UUID = None,
    email: str = "test@x.com",
    password: str = "pass123",
    full_name: str = "Test User",
    is_active: bool = True,
    email_verified: bool = False,
):
    user = MagicMock()
    user.id = uid or uuid.uuid4()
    user.email = email
    user.password_hash = hash_password(password)
    user.full_name = full_name
    user.is_active = is_active
    user.email_verified = email_verified
    user.phone = None
    user.last_login_at = None
    return user


def _mock_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.invalidate_existing_pins = AsyncMock()
    repo.create_pin = AsyncMock()
    repo.mark_pin_used = AsyncMock()
    repo.get_user_properties = AsyncMock(return_value=[])
    return repo


def _mock_role(role_name: str = "admin"):
    role = MagicMock()
    role.id = uuid.uuid4()
    role.role_name = role_name
    return role


def _mock_condo(name: str = "Condo A"):
    condo = MagicMock()
    condo.id = uuid.uuid4()
    condo.name = name
    return condo


# ══════════════════════════════════════════════════════════════════════════
#  Login step 1
# ══════════════════════════════════════════════════════════════════════════


class TestLoginStep1:
    @pytest.mark.asyncio
    async def test_success(self):
        user = _mock_user(password="correct")
        condo = _mock_condo()
        role = _mock_role("admin")
        ucr = MagicMock()

        repo = _mock_repo()
        repo.get_user_by_email = AsyncMock(return_value=user)
        repo.get_user_condominium_roles = AsyncMock(return_value=[(ucr, condo, role)])

        svc = AuthService(repo)
        body = LoginRequest(email="test@x.com", password="correct")
        result = await svc.login_step1(body)

        assert result.user_id == user.id
        assert result.access_token is not None
        assert len(result.condominiums) == 1

    @pytest.mark.asyncio
    async def test_wrong_password(self):
        user = _mock_user(password="correct")
        repo = _mock_repo()
        repo.get_user_by_email = AsyncMock(return_value=user)

        svc = AuthService(repo)
        body = LoginRequest(email="test@x.com", password="wrong")

        with pytest.raises(UnauthorizedError, match="Credenciales inválidas"):
            await svc.login_step1(body)

    @pytest.mark.asyncio
    async def test_user_not_found(self):
        repo = _mock_repo()
        repo.get_user_by_email = AsyncMock(return_value=None)

        svc = AuthService(repo)
        body = LoginRequest(email="no@x.com", password="whatever")

        with pytest.raises(UnauthorizedError):
            await svc.login_step1(body)

    @pytest.mark.asyncio
    async def test_inactive_user(self):
        user = _mock_user(password="pass", is_active=False)
        repo = _mock_repo()
        repo.get_user_by_email = AsyncMock(return_value=user)
        repo.get_user_condominium_roles = AsyncMock(return_value=[])

        svc = AuthService(repo)
        body = LoginRequest(email="test@x.com", password="pass")

        with pytest.raises(ForbiddenError, match="inactivo"):
            await svc.login_step1(body)


# ══════════════════════════════════════════════════════════════════════════
#  Login step 2
# ══════════════════════════════════════════════════════════════════════════


class TestLoginStep2:
    @pytest.mark.asyncio
    async def test_success_single_condo(self):
        user = _mock_user()
        condo = _mock_condo()
        role = _mock_role("admin")
        ucr = MagicMock()

        repo = _mock_repo()
        repo.get_user_by_email = AsyncMock(return_value=user)
        repo.get_valid_pin = AsyncMock(return_value=MagicMock())
        repo.get_user_condominium_roles = AsyncMock(return_value=[(ucr, condo, role)])

        svc = AuthService(repo)
        body = VerifyLoginPinRequest(email="test@x.com", pin="123456")
        result = await svc.login_step2(body)

        assert result.user_id == user.id
        assert result.access_token is not None
        assert len(result.condominiums) == 1
        assert result.condominiums[0].role == "admin"

    @pytest.mark.asyncio
    async def test_success_multiple_condos(self):
        user = _mock_user()
        condo1 = _mock_condo("Condo A")
        condo2 = _mock_condo("Condo B")
        role = _mock_role("admin")

        repo = _mock_repo()
        repo.get_user_by_email = AsyncMock(return_value=user)
        repo.get_valid_pin = AsyncMock(return_value=MagicMock())
        repo.get_user_condominium_roles = AsyncMock(
            return_value=[(MagicMock(), condo1, role), (MagicMock(), condo2, role)]
        )
        repo.get_user_properties = AsyncMock(return_value=[])

        svc = AuthService(repo)
        body = VerifyLoginPinRequest(email="test@x.com", pin="123456")
        result = await svc.login_step2(body)

        assert len(result.condominiums) == 2
        assert "Seleccione" in result.message

    @pytest.mark.asyncio
    async def test_invalid_pin(self):
        user = _mock_user()
        repo = _mock_repo()
        repo.get_user_by_email = AsyncMock(return_value=user)
        repo.get_valid_pin = AsyncMock(return_value=None)

        svc = AuthService(repo)
        body = VerifyLoginPinRequest(email="test@x.com", pin="000000")

        with pytest.raises(BadRequestError, match="inválido"):
            await svc.login_step2(body)


# ══════════════════════════════════════════════════════════════════════════
#  Password reset
# ══════════════════════════════════════════════════════════════════════════


class TestPasswordReset:
    @patch("app.modules.auth.service.send_pin_email")
    @pytest.mark.asyncio
    async def test_request_reset(self, mock_send):
        user = _mock_user()
        repo = _mock_repo()
        repo.get_user_by_email = AsyncMock(return_value=user)

        svc = AuthService(repo)
        body = RequestPasswordResetRequest(email="test@x.com")
        result = await svc.request_password_reset(body)

        # silent_on_missing returns a generic message regardless of email existence
        assert "recibirás un código" in result["message"]
        mock_send.assert_called_once()

    @patch("app.modules.auth.service.send_pin_email")
    @pytest.mark.asyncio
    async def test_request_reset_unknown_email_silent(self, mock_send):
        """forgot-password should not reveal if the email exists."""
        repo = _mock_repo()
        repo.get_user_by_email = AsyncMock(return_value=None)

        svc = AuthService(repo)
        body = RequestPasswordResetRequest(email="nope@x.com")
        result = await svc.request_password_reset(body)

        assert "recibirás un código" in result["message"]
        mock_send.assert_not_called()

    @patch(
        "app.modules.auth.service.send_pin_email",
        side_effect=Exception("SMTP down"),
    )
    @pytest.mark.asyncio
    async def test_request_reset_smtp_failure_doesnt_500(self, mock_send):
        """If SMTP fails, the endpoint must still return 200 (PIN is in DB)."""
        user = _mock_user()
        repo = _mock_repo()
        repo.get_user_by_email = AsyncMock(return_value=user)

        svc = AuthService(repo)
        body = RequestPasswordResetRequest(email="test@x.com")
        result = await svc.request_password_reset(body)

        assert "recibirás un código" in result["message"]

    @pytest.mark.asyncio
    async def test_reset_password_success(self):
        user = _mock_user()
        repo = _mock_repo()
        repo.get_user_by_email = AsyncMock(return_value=user)
        repo.get_valid_pin = AsyncMock(return_value=MagicMock())

        svc = AuthService(repo)
        body = ResetPasswordRequest(email="test@x.com", pin="123456", new_password="newpass")
        result = await svc.reset_password(body)

        assert "restablecida" in result["message"]
        assert verify_password("newpass", user.password_hash)

    @pytest.mark.asyncio
    async def test_reset_password_bad_pin(self):
        user = _mock_user()
        repo = _mock_repo()
        repo.get_user_by_email = AsyncMock(return_value=user)
        repo.get_valid_pin = AsyncMock(return_value=None)

        svc = AuthService(repo)
        body = ResetPasswordRequest(email="test@x.com", pin="wrong", new_password="new")

        with pytest.raises(BadRequestError):
            await svc.reset_password(body)


# ══════════════════════════════════════════════════════════════════════════
#  Email verification
# ══════════════════════════════════════════════════════════════════════════


class TestEmailVerification:
    @patch("app.modules.auth.service.send_pin_email")
    @pytest.mark.asyncio
    async def test_request_verify(self, mock_send):
        user = _mock_user()
        repo = _mock_repo()
        repo.get_user_by_email = AsyncMock(return_value=user)

        svc = AuthService(repo)
        body = RequestPinRequest(email="test@x.com", pin_type="verify_email")
        result = await svc.request_verify_email(body)

        assert "Código enviado" in result["message"]

    @pytest.mark.asyncio
    async def test_verify_email_success(self):
        user = _mock_user(email_verified=False)
        repo = _mock_repo()
        repo.get_user_by_email = AsyncMock(return_value=user)
        repo.get_valid_pin = AsyncMock(return_value=MagicMock())

        svc = AuthService(repo)
        body = VerifyEmailRequest(email="test@x.com", pin="123456")
        result = await svc.verify_email(body)

        assert "verificado" in result["message"]
        assert user.email_verified is True


# ══════════════════════════════════════════════════════════════════════════
#  Select condominium
# ══════════════════════════════════════════════════════════════════════════


class TestSelectCondominium:
    @pytest.mark.asyncio
    async def test_success(self):
        role = _mock_role("admin")
        ucr = MagicMock()
        repo = _mock_repo()
        repo.get_user_role_in_condominium = AsyncMock(return_value=(ucr, role))

        svc = AuthService(repo)
        cid = uuid.uuid4()
        body = SelectCondominiumRequest(condominium_id=cid)
        result = await svc.select_condominium(body, str(uuid.uuid4()))

        assert result.access_token is not None
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_not_member(self):
        repo = _mock_repo()
        repo.get_user_role_in_condominium = AsyncMock(return_value=None)

        svc = AuthService(repo)
        body = SelectCondominiumRequest(condominium_id=uuid.uuid4())

        with pytest.raises(ForbiddenError, match="No pertenece"):
            await svc.select_condominium(body, str(uuid.uuid4()))


# ══════════════════════════════════════════════════════════════════════════
#  Change password
# ══════════════════════════════════════════════════════════════════════════


class TestChangePassword:
    @pytest.mark.asyncio
    async def test_success(self):
        user = _mock_user(password="oldpass")
        repo = _mock_repo()
        repo.get_user_by_id = AsyncMock(return_value=user)

        svc = AuthService(repo)
        body = ChangePasswordRequest(current_password="oldpass", new_password="newpass")
        await svc.change_password(user.id, body)

        assert verify_password("newpass", user.password_hash)
        repo.save.assert_called()

    @pytest.mark.asyncio
    async def test_wrong_current(self):
        user = _mock_user(password="correct")
        repo = _mock_repo()
        repo.get_user_by_id = AsyncMock(return_value=user)

        svc = AuthService(repo)
        body = ChangePasswordRequest(current_password="wrong", new_password="new")

        with pytest.raises(BadRequestError, match="incorrecta"):
            await svc.change_password(user.id, body)


# ══════════════════════════════════════════════════════════════════════════
#  Get me
# ══════════════════════════════════════════════════════════════════════════


class TestGetMe:
    @pytest.mark.asyncio
    async def test_returns_user_data(self):
        user = _mock_user()
        condo = _mock_condo()
        role = _mock_role()

        repo = _mock_repo()
        repo.get_user_condominium_roles = AsyncMock(
            return_value=[(MagicMock(), condo, role)]
        )
        repo.get_user_properties = AsyncMock(return_value=[])

        svc = AuthService(repo)
        result = await svc.get_me(user, "fake_token")

        assert result.user_id == user.id
        assert result.email == user.email
        assert result.access_token == "fake_token"
        assert len(result.condominiums) == 1
