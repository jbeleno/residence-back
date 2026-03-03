"""FastAPI dependencies: auth, tenant scoping, role checking."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token

# Lazy import to avoid circular dependency at module level
_User = None


def _get_user_model():
    global _User
    if _User is None:
        from app.models.core import User
        _User = User
    return _User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Current user ──────────────────────────────────────────────────────────


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Decode JWT and return the active ``User`` ORM instance."""
    from sqlalchemy import select

    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedError("Token inválido o expirado")

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Token inválido")

    User = _get_user_model()
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalars().first()
    if user is None or not user.is_active:
        raise UnauthorizedError("Usuario no encontrado o inactivo")
    return user


# ── Condominium scope ────────────────────────────────────────────────────


async def get_current_condominium_id(
    token: str = Depends(oauth2_scheme),
) -> UUID:
    """Extract ``cid`` (condominium_id) from the scoped JWT."""
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedError("Token inválido o expirado")

    cid = payload.get("cid")
    if cid is None:
        raise ForbiddenError("Token sin alcance de condominio. Use /auth/select-condominium.")
    return UUID(cid)


# ── Role ──────────────────────────────────────────────────────────────────


async def get_current_role(
    token: str = Depends(oauth2_scheme),
) -> str:
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedError("Token inválido o expirado")
    role = payload.get("role")
    if role is None:
        raise ForbiddenError("Token sin rol asignado")
    return role


# ── Role checker (reusable) ──────────────────────────────────────────────


class RoleChecker:
    """Dependency class that verifies the caller has one of the allowed roles."""

    def __init__(self, allowed_roles: list[str]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(self, role: str = Depends(get_current_role)) -> str:
        if role not in self.allowed_roles:
            raise ForbiddenError("Rol insuficiente para esta acción")
        return role


# Pre-built role checkers
require_super_admin = RoleChecker(["super_admin"])
require_admin = RoleChecker(["super_admin", "admin"])
require_admin_or_guard = RoleChecker(["super_admin", "admin", "guarda"])
require_admin_or_accountant = RoleChecker(["super_admin", "admin", "contador"])
require_authenticated = RoleChecker(["super_admin", "admin", "guarda", "residente", "contador"])
