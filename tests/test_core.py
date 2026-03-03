"""Tests for core utilities: security, responses, exceptions, config, email."""

from __future__ import annotations

import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    InternalError,
    NotFoundError,
    TenantAccessError,
    UnauthorizedError,
)
from app.core.responses import PaginationMeta, PaginationParams, success, success_list
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# ══════════════════════════════════════════════════════════════════════════
#  Security
# ══════════════════════════════════════════════════════════════════════════


class TestPasswordHashing:
    def test_hash_and_verify(self):
        raw = "my_secret_123"
        hashed = hash_password(raw)
        assert hashed != raw
        assert verify_password(raw, hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_different_hashes(self):
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2  # bcrypt salts differ


class TestJWT:
    def test_create_and_decode(self):
        uid = str(uuid.uuid4())
        token = create_access_token({"sub": uid, "role": "admin"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == uid
        assert payload["role"] == "admin"
        assert "exp" in payload

    def test_custom_expiry(self):
        token = create_access_token(
            {"sub": "u1"}, expires_delta=timedelta(minutes=1)
        )
        payload = decode_access_token(token)
        assert payload is not None

    def test_invalid_token_returns_none(self):
        assert decode_access_token("not.a.valid.token") is None
        assert decode_access_token("") is None

    def test_expired_token(self):
        token = create_access_token(
            {"sub": "u1"}, expires_delta=timedelta(seconds=-1)
        )
        assert decode_access_token(token) is None

    def test_token_with_cid(self):
        cid = str(uuid.uuid4())
        token = create_access_token({"sub": "u1", "cid": cid, "role": "admin"})
        payload = decode_access_token(token)
        assert payload["cid"] == cid


# ══════════════════════════════════════════════════════════════════════════
#  Responses
# ══════════════════════════════════════════════════════════════════════════


class TestResponses:
    def test_success_simple(self):
        result = success({"key": "value"})
        assert result["status"] == "success"
        assert result["data"] == {"key": "value"}
        assert "meta" not in result

    def test_success_with_meta(self):
        meta = PaginationMeta(page=2, page_size=10, total=50)
        result = success([1, 2, 3], meta=meta)
        assert result["status"] == "success"
        assert result["data"] == [1, 2, 3]
        assert result["meta"]["page"] == 2
        assert result["meta"]["total"] == 50

    def test_success_list(self):
        result = success_list(["a", "b"], total=100, page=3, page_size=25)
        assert result["status"] == "success"
        assert result["data"] == ["a", "b"]
        assert result["meta"]["total"] == 100
        assert result["meta"]["page"] == 3

    def test_success_empty(self):
        result = success(None)
        assert result["status"] == "success"
        assert result["data"] is None


class TestPaginationParams:
    def test_defaults(self):
        p = PaginationParams()
        assert p.page == 1
        assert p.page_size == 50
        assert p.offset == 0
        assert p.limit == 50

    def test_custom(self):
        p = PaginationParams(page=3, page_size=20)
        assert p.offset == 40
        assert p.limit == 20


# ══════════════════════════════════════════════════════════════════════════
#  Exceptions
# ══════════════════════════════════════════════════════════════════════════


class TestExceptions:
    def test_bad_request(self):
        e = BadRequestError("campo inválido")
        assert e.status_code == 400
        assert e.code == "BAD_REQUEST"
        assert e.message == "campo inválido"

    def test_unauthorized(self):
        e = UnauthorizedError()
        assert e.status_code == 401
        assert e.code == "UNAUTHORIZED"

    def test_forbidden(self):
        e = ForbiddenError()
        assert e.status_code == 403

    def test_not_found(self):
        e = NotFoundError("no existe")
        assert e.status_code == 404
        assert str(e) == "no existe"

    def test_conflict(self):
        e = ConflictError()
        assert e.status_code == 409

    def test_tenant_access(self):
        e = TenantAccessError()
        assert e.status_code == 403
        assert e.code == "TENANT_ACCESS_DENIED"

    def test_internal(self):
        e = InternalError()
        assert e.status_code == 500

    def test_custom_override(self):
        e = AppException("custom", code="CUSTOM", status_code=422)
        assert e.status_code == 422
        assert e.code == "CUSTOM"
        assert e.message == "custom"

    def test_is_exception(self):
        e = NotFoundError()
        assert isinstance(e, Exception)
        assert isinstance(e, AppException)


# ══════════════════════════════════════════════════════════════════════════
#  Config
# ══════════════════════════════════════════════════════════════════════════


class TestConfig:
    def test_settings_loaded(self):
        assert settings.SECRET_KEY is not None
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0

    def test_cors_list(self):
        origins = settings.cors_origins_list
        assert isinstance(origins, list)

    def test_app_info(self):
        assert settings.APP_NAME != ""
        assert settings.APP_VERSION != ""


# ══════════════════════════════════════════════════════════════════════════
#  Email helpers (unit-test without SMTP)
# ══════════════════════════════════════════════════════════════════════════


class TestEmailHelpers:
    def test_generate_pin_length(self):
        from app.core.email import generate_pin

        pin = generate_pin()
        assert len(pin) == 6
        assert pin.isdigit()

    def test_generate_pin_custom_length(self):
        from app.core.email import generate_pin

        pin = generate_pin(length=4)
        assert len(pin) == 4

    @patch("app.core.email.smtplib.SMTP")
    def test_send_pin_email(self, mock_smtp):
        from app.core.email import send_pin_email

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        send_pin_email("test@x.com", "123456", "login", "John")
        mock_smtp.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════
#  AI helpers (unit-test without API calls)
# ══════════════════════════════════════════════════════════════════════════


class TestAIHelpers:
    @patch("app.core.ai._get_client")
    @pytest.mark.asyncio
    async def test_get_embedding(self, mock_client_fn):
        from app.core.ai import get_embedding

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1] * 768
        mock_response.embeddings = [mock_embedding]
        mock_client.models.embed_content.return_value = mock_response
        mock_client_fn.return_value = mock_client

        result = await get_embedding("test text")
        assert len(result) == 768
        assert result[0] == 0.1

    @patch("app.core.ai._get_client")
    @pytest.mark.asyncio
    async def test_chat_completion(self, mock_client_fn):
        from app.core.ai import chat_completion

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Hola, soy Resi."
        mock_client.models.generate_content.return_value = mock_response
        mock_client_fn.return_value = mock_client

        result = await chat_completion("system", [], "Hola")
        assert result == "Hola, soy Resi."

    @patch("app.core.ai._get_client")
    @pytest.mark.asyncio
    async def test_chat_completion_no_text(self, mock_client_fn):
        from app.core.ai import chat_completion

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = None
        mock_client.models.generate_content.return_value = mock_response
        mock_client_fn.return_value = mock_client

        result = await chat_completion("system", [], "test")
        assert result == "No pude generar una respuesta."
