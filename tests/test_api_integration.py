"""Integration tests – full HTTP round-trips through the FastAPI app.

These tests exercise the real routers, middleware, serialisation,
error-handling, and auth dependencies by overriding DI at the
service / dependency level.  No real database is touched.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token


# ── Helpers ───────────────────────────────────────────────────────────────

def _uid() -> uuid.UUID:
    return uuid.uuid4()


def _cid() -> uuid.UUID:
    return uuid.uuid4()


def _fake_user(uid=None, email="user@test.com", full_name="Tester"):
    u = MagicMock()
    u.id = uid or _uid()
    u.email = email
    u.full_name = full_name
    u.is_active = True
    u.email_verified = True
    return u


def _fake_condo_out(cid=None, name="TestCondo"):
    """Return a real CondominiumOut so model_validate() in the router works."""
    from app.schemas.condominium import CondominiumOut
    return CondominiumOut(
        id=cid or _cid(),
        name=name,
        address="Addr",
        city="City",
        country="CO",
        timezone="America/Bogota",
        currency="COP",
        visitor_parking_hourly_rate=0,
        created_at="2024-01-01T00:00:00",
    )


# ── App factory with dependency overrides ─────────────────────────────────

def _create_test_app(
    *,
    user=None,
    cid=None,
    role="admin",
    auth_svc=None,
    condo_svc=None,
    chatbot_svc=None,
    user_svc=None,
    property_svc=None,
    finance_svc=None,
    visitor_svc=None,
    notification_svc=None,
):
    """Build a FastAPI app with services / auth mocked out."""
    from app.main import create_app
    from app.core.database import get_db
    from app.core.dependencies import (
        get_current_user,
        get_current_condominium_id,
        get_current_role,
        require_super_admin,
        require_admin,
        require_admin_or_guard,
        require_admin_or_accountant,
        require_authenticated,
    )

    app = create_app()

    # Fake DB — never actually used because services are overridden
    async def _fake_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = _fake_db

    # Auth overrides
    if user:
        app.dependency_overrides[get_current_user] = lambda: user
    if cid:
        app.dependency_overrides[get_current_condominium_id] = lambda: cid
    if role:
        app.dependency_overrides[get_current_role] = lambda: role

    # Role checkers – just pass through
    for checker in [
        require_super_admin, require_admin,
        require_admin_or_guard, require_admin_or_accountant,
        require_authenticated,
    ]:
        app.dependency_overrides[checker] = lambda: role

    # Service overrides
    if auth_svc:
        from app.modules.auth.router import _service as _auth_svc
        app.dependency_overrides[_auth_svc] = lambda: auth_svc

    if condo_svc:
        from app.modules.condominiums.router import _service as _condo_svc
        app.dependency_overrides[_condo_svc] = lambda: condo_svc

    if chatbot_svc:
        from app.modules.chatbot.router import _service as _chatbot_svc
        app.dependency_overrides[_chatbot_svc] = lambda: chatbot_svc

    if user_svc:
        from app.modules.users.router import _service as _user_svc
        app.dependency_overrides[_user_svc] = lambda: user_svc

    if property_svc:
        from app.modules.properties.router import _service as _prop_svc
        app.dependency_overrides[_prop_svc] = lambda: property_svc

    if finance_svc:
        from app.modules.finance.router import _service as _fin_svc
        app.dependency_overrides[_fin_svc] = lambda: finance_svc

    if visitor_svc:
        from app.modules.visitors.router import _service as _vis_svc
        app.dependency_overrides[_vis_svc] = lambda: visitor_svc

    if notification_svc:
        from app.modules.notifications.router import _service as _notif_svc
        app.dependency_overrides[_notif_svc] = lambda: notification_svc

    return app


# ══════════════════════════════════════════════════════════════════════════
#  App / OpenAPI
# ══════════════════════════════════════════════════════════════════════════


class TestApp:
    @pytest.mark.asyncio
    async def test_openapi_spec(self):
        app = _create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/openapi.json")
        assert r.status_code == 200
        assert "paths" in r.json()

    @pytest.mark.asyncio
    async def test_404_unknown_route(self):
        app = _create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/nonexistent")
        assert r.status_code in (404, 405)


# ══════════════════════════════════════════════════════════════════════════
#  Auth endpoints
# ══════════════════════════════════════════════════════════════════════════


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_login_no_body(self):
        app = _create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post("/api/v1/auth/login")
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_login_step1_success(self):
        from app.schemas.auth import LoginDataOut
        svc = AsyncMock()
        svc.login_step1.return_value = LoginDataOut(
            user_id=_uid(),
            full_name="Test User",
            email="a@b.com",
            access_token="fake_token",
        )

        app = _create_test_app(auth_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post("/api/v1/auth/login", json={
                "email": "a@b.com", "password": "secret",
            })
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "success"
        assert body["data"]["access_token"] == "fake_token"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self):
        from app.core.exceptions import UnauthorizedError

        svc = AsyncMock()
        svc.login_step1.side_effect = UnauthorizedError("Credenciales inválidas")

        app = _create_test_app(auth_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post("/api/v1/auth/login", json={
                "email": "a@b.com", "password": "wrong",
            })
        assert r.status_code == 401
        assert r.json()["status"] == "error"

    @pytest.mark.asyncio
    async def test_me_no_token(self):
        from app.main import create_app
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/auth/me")
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_me_success(self):
        user = _fake_user()
        from app.schemas.auth import LoginDataOut, CondominiumRoleOut
        me_data = LoginDataOut(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            access_token="tok",
            condominiums=[
                CondominiumRoleOut(
                    condominium_id=_cid(),
                    condominium_name="C1",
                    role="admin",
                )
            ],
        )
        svc = AsyncMock()
        svc.get_me.return_value = me_data

        from app.core.dependencies import oauth2_scheme
        app = _create_test_app(user=user, cid=_cid(), auth_svc=svc)
        app.dependency_overrides[oauth2_scheme] = lambda: "fake_token"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/auth/me")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["email"] == user.email

    @pytest.mark.asyncio
    async def test_change_password_returns_success(self):
        user = _fake_user()
        svc = AsyncMock()
        svc.change_password.return_value = None

        app = _create_test_app(user=user, cid=_cid(), auth_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post("/api/v1/auth/change-password", json={
                "current_password": "old", "new_password": "new",
            })
        assert r.status_code == 200
        assert "actualizada" in r.json()["data"]["message"]


# ══════════════════════════════════════════════════════════════════════════
#  Condominiums CRUD
# ══════════════════════════════════════════════════════════════════════════


class TestCondominiumEndpoints:
    @pytest.mark.asyncio
    async def test_get_current_condominium(self):
        cid = _cid()
        condo = _fake_condo_out(cid=cid, name="MyCondo")

        svc = AsyncMock()
        svc.get_current.return_value = condo

        app = _create_test_app(
            user=_fake_user(), cid=cid, role="admin", condo_svc=svc,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/condominiums/current")
        assert r.status_code == 200
        assert r.json()["data"]["name"] == "MyCondo"

    @pytest.mark.asyncio
    async def test_create_condominium_super_admin(self):
        new_condo = _fake_condo_out(name="NuevoCondo")
        svc = AsyncMock()
        svc.create.return_value = new_condo

        app = _create_test_app(
            user=_fake_user(), cid=_cid(), role="super_admin", condo_svc=svc,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post("/api/v1/condominiums/", json={
                "name": "NuevoCondo", "address": "Calle 2",
            })
        assert r.status_code == 201
        assert r.json()["data"]["name"] == "NuevoCondo"

    @pytest.mark.asyncio
    async def test_create_condominium_forbidden(self):
        """Without role override, real role check rejects (no token → 401)."""
        from app.main import create_app
        from app.core.database import get_db

        app = create_app()

        async def _fake_db():
            yield AsyncMock()

        app.dependency_overrides[get_db] = _fake_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post("/api/v1/condominiums/", json={"name": "X"})
        assert r.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_update_condominium(self):
        cid = _cid()
        updated = _fake_condo_out(cid=cid, name="NewName")
        svc = AsyncMock()
        svc.update.return_value = updated

        app = _create_test_app(
            user=_fake_user(), cid=cid, role="admin", condo_svc=svc,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.patch("/api/v1/condominiums/current", json={
                "name": "NewName",
            })
        assert r.status_code == 200
        assert r.json()["data"]["name"] == "NewName"


# ══════════════════════════════════════════════════════════════════════════
#  Chatbot endpoints
# ══════════════════════════════════════════════════════════════════════════


class TestChatbotEndpoints:
    @pytest.mark.asyncio
    async def test_condominium_info(self):
        cid = _cid()
        svc = AsyncMock()
        svc.condominium_info.return_value = {
            "name": "TestCondo", "total_properties": 0,
        }

        app = _create_test_app(user=_fake_user(), cid=cid, chatbot_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/chatbot/condominium-info")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["name"] == "TestCondo"
        assert data["total_properties"] == 0

    @pytest.mark.asyncio
    async def test_amenities_summary_empty(self):
        svc = AsyncMock()
        svc.amenities_summary.return_value = []

        app = _create_test_app(user=_fake_user(), cid=_cid(), chatbot_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/chatbot/amenities-summary")
        assert r.status_code == 200
        assert r.json()["data"] == []

    @pytest.mark.asyncio
    async def test_finance_summary_empty(self):
        svc = AsyncMock()
        svc.finance_summary.return_value = {"total_invoices": 0}

        app = _create_test_app(user=_fake_user(), cid=_cid(), chatbot_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/chatbot/finance-summary")
        assert r.status_code == 200
        assert r.json()["data"]["total_invoices"] == 0

    @pytest.mark.asyncio
    async def test_latest_news_empty(self):
        svc = AsyncMock()
        svc.latest_news_summary.return_value = []

        app = _create_test_app(user=_fake_user(), cid=_cid(), chatbot_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/chatbot/latest-news")
        assert r.status_code == 200
        assert r.json()["data"] == []

    @pytest.mark.asyncio
    async def test_parking_summary_empty(self):
        svc = AsyncMock()
        svc.parking_summary.return_value = {"total_spaces": 0}

        app = _create_test_app(user=_fake_user(), cid=_cid(), chatbot_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/chatbot/parking-summary")
        assert r.status_code == 200
        assert r.json()["data"]["total_spaces"] == 0

    @pytest.mark.asyncio
    async def test_pets_summary_empty(self):
        svc = AsyncMock()
        svc.pets_summary.return_value = {"total_pets": 0}

        app = _create_test_app(user=_fake_user(), cid=_cid(), chatbot_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/chatbot/pets-summary")
        assert r.status_code == 200
        assert r.json()["data"]["total_pets"] == 0

    @pytest.mark.asyncio
    async def test_short_rent_empty(self):
        svc = AsyncMock()
        svc.short_rent_properties.return_value = []

        app = _create_test_app(user=_fake_user(), cid=_cid(), chatbot_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/chatbot/short-rent-properties")
        assert r.status_code == 200
        assert r.json()["data"] == []

    @pytest.mark.asyncio
    async def test_chat_no_auth(self):
        from app.main import create_app
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post("/api/v1/chatbot/chat", json={"message": "hi"})
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_documents_requires_admin(self):
        """Without role override → 401 (no token)."""
        from app.main import create_app
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/chatbot/documents")
        assert r.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_sessions_list_empty(self):
        user = _fake_user()
        svc = AsyncMock()
        svc.list_sessions.return_value = []

        app = _create_test_app(user=user, cid=_cid(), chatbot_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/chatbot/sessions")
        assert r.status_code == 200
        assert r.json()["data"] == []


# ══════════════════════════════════════════════════════════════════════════
#  Error response contract
# ══════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════
#  User endpoints
# ══════════════════════════════════════════════════════════════════════════


class TestUserEndpoints:
    def _user_out(self, uid=None) -> dict:
        from app.schemas.user import UserOut
        return UserOut(
            id=uid or _uid(),
            full_name="Test User",
            email="t@t.com",
            is_active=True,
            email_verified=False,
        )

    @pytest.mark.asyncio
    async def test_list_users(self):
        svc = AsyncMock()
        u = self._user_out()
        svc.list_users.return_value = [u]

        app = _create_test_app(user=_fake_user(), cid=_cid(), role="admin", user_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/users/")
        assert r.status_code == 200
        assert len(r.json()["data"]) == 1

    @pytest.mark.asyncio
    async def test_get_user(self):
        uid = _uid()
        svc = AsyncMock()
        svc.get_user.return_value = self._user_out(uid=uid)

        app = _create_test_app(user=_fake_user(), cid=_cid(), user_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get(f"/api/v1/users/{uid}")
        assert r.status_code == 200
        assert r.json()["data"]["full_name"] == "Test User"

    @pytest.mark.asyncio
    async def test_create_user(self):
        svc = AsyncMock()
        svc.create_user.return_value = self._user_out()

        app = _create_test_app(user=_fake_user(), cid=_cid(), role="admin", user_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post("/api/v1/users/", json={
                "full_name": "New", "email": "n@n.com", "password": "secret",
            })
        assert r.status_code == 201


# ══════════════════════════════════════════════════════════════════════════
#  Property endpoints
# ══════════════════════════════════════════════════════════════════════════


class TestPropertyEndpoints:
    @pytest.mark.asyncio
    async def test_list_properties(self):
        svc = AsyncMock()
        svc.list_properties.return_value = [{"id": str(_uid()), "number": "101"}]

        app = _create_test_app(user=_fake_user(), cid=_cid(), property_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/properties/")
        assert r.status_code == 200
        assert len(r.json()["data"]) == 1

    @pytest.mark.asyncio
    async def test_create_property(self):
        svc = AsyncMock()
        svc.create_property.return_value = {"id": str(_uid()), "number": "201"}

        app = _create_test_app(user=_fake_user(), cid=_cid(), role="admin", property_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post("/api/v1/properties/", json={
                "number": "201", "property_type_id": 1,
            })
        assert r.status_code == 201

    @pytest.mark.asyncio
    async def test_list_residents(self):
        pid = _uid()
        svc = AsyncMock()
        svc.list_residents.return_value = [{"id": 1, "user_full_name": "A"}]

        app = _create_test_app(user=_fake_user(), cid=_cid(), property_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get(f"/api/v1/properties/{pid}/residents")
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
#  Finance endpoints
# ══════════════════════════════════════════════════════════════════════════


class TestFinanceEndpoints:
    @pytest.mark.asyncio
    async def test_list_invoices(self):
        svc = AsyncMock()
        svc.list_invoices.return_value = [{"id": str(_uid()), "amount": 100}]

        app = _create_test_app(user=_fake_user(), cid=_cid(), finance_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/finance/invoices")
        assert r.status_code == 200
        assert len(r.json()["data"]) == 1

    @pytest.mark.asyncio
    async def test_get_property_balance(self):
        pid = _uid()
        svc = AsyncMock()
        svc.get_property_balance.return_value = {
            "property_id": str(pid), "total_charged": 300,
            "total_paid": 200, "total_pending": 100, "invoice_count": 2,
        }

        app = _create_test_app(user=_fake_user(), cid=_cid(), finance_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get(f"/api/v1/finance/property-balance/{pid}")
        assert r.status_code == 200
        assert r.json()["data"]["total_pending"] == 100

    @pytest.mark.asyncio
    async def test_mark_overdue(self):
        svc = AsyncMock()
        svc.mark_overdue.return_value = None

        app = _create_test_app(user=_fake_user(), cid=_cid(), role="admin", finance_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post("/api/v1/finance/mark-overdue")
        assert r.status_code == 200
        assert "actualizadas" in r.json()["data"]["message"]


# ══════════════════════════════════════════════════════════════════════════
#  Visitor endpoints
# ══════════════════════════════════════════════════════════════════════════


class TestVisitorEndpoints:
    @pytest.mark.asyncio
    async def test_list_visitors(self):
        svc = AsyncMock()
        svc.list_visitors.return_value = [{"id": str(_uid()), "visitor_name": "Juan"}]

        app = _create_test_app(user=_fake_user(), cid=_cid(), visitor_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/visitors/")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_list_active(self):
        svc = AsyncMock()
        svc.list_active.return_value = []

        app = _create_test_app(user=_fake_user(), cid=_cid(), visitor_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/visitors/active")
        assert r.status_code == 200
        assert r.json()["data"] == []

    @pytest.mark.asyncio
    async def test_register_entry(self):
        svc = AsyncMock()
        svc.register_entry.return_value = {"id": str(_uid()), "visitor_name": "Maria"}

        app = _create_test_app(user=_fake_user(), cid=_cid(), role="admin", visitor_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post("/api/v1/visitors/", json={
                "property_id": str(_uid()), "visitor_name": "Maria",
            })
        assert r.status_code == 201

    @pytest.mark.asyncio
    async def test_register_exit(self):
        vid = _uid()
        svc = AsyncMock()
        svc.register_exit.return_value = {"id": str(vid), "exit_time": "2025-03-01T15:00:00"}

        app = _create_test_app(user=_fake_user(), cid=_cid(), role="admin", visitor_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post(f"/api/v1/visitors/{vid}/exit")
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
#  Notification endpoints
# ══════════════════════════════════════════════════════════════════════════


class TestNotificationEndpoints:
    @pytest.mark.asyncio
    async def test_list_my_notifications(self):
        svc = AsyncMock()
        svc.list_my_notifications.return_value = [{"title": "Pago"}]

        app = _create_test_app(user=_fake_user(), cid=_cid(), notification_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/notifications/me")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_unread_count(self):
        svc = AsyncMock()
        svc.unread_count.return_value = {"unread_count": 3}

        app = _create_test_app(user=_fake_user(), cid=_cid(), notification_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/notifications/me/unread-count")
        assert r.status_code == 200
        assert r.json()["data"]["unread_count"] == 3

    @pytest.mark.asyncio
    async def test_mark_all_read(self):
        svc = AsyncMock()
        svc.mark_all_read.return_value = {"message": "2 notificación(es) marcada(s) como leída(s)"}

        app = _create_test_app(user=_fake_user(), cid=_cid(), notification_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post("/api/v1/notifications/me/mark-all-read")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_send_notification_admin(self):
        svc = AsyncMock()
        svc.send_notification.return_value = {"id": str(_uid()), "title": "Test"}

        app = _create_test_app(user=_fake_user(), cid=_cid(), role="admin", notification_svc=svc)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post("/api/v1/notifications/send", json={
                "user_id": str(_uid()), "notification_type_id": 1,
                "title": "Test", "body": "Test body",
            })
        assert r.status_code == 201


class TestErrorContract:
    @pytest.mark.asyncio
    async def test_unauthorized_response(self):
        from app.main import create_app
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/v1/auth/me")
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_validation_error(self):
        from app.main import create_app
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post("/api/v1/auth/login", json={"email": "not-an-email"})
        assert r.status_code == 422
