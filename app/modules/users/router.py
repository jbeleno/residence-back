"""User router."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    get_current_condominium_id,
    get_current_role,
    get_current_user,
    require_admin,
    require_authenticated,
    require_super_admin,
    require_super_admin_user,
)
from app.core.exceptions import ForbiddenError
from app.core.responses import success
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService
from app.schemas.user import (
    UserCreate,
    UserCreateResponse,
    UserDeviceCreate,
    UserDeviceOut,
    UserOut,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["Usuarios"])


def _service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.get("/", dependencies=[Depends(require_admin)])
async def list_users(
    cid: UUID = Depends(get_current_condominium_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    svc: UserService = Depends(_service),
):
    users = await svc.list_users(cid, skip, limit)
    return success([UserOut.model_validate(u).model_dump() for u in users])


@router.get("/{user_id}", dependencies=[Depends(require_authenticated)])
async def get_user(user_id: UUID, svc: UserService = Depends(_service)):
    user = await svc.get_user(user_id)
    return success(UserOut.model_validate(user).model_dump())


@router.post("/", dependencies=[Depends(require_admin)], status_code=201)
async def create_user(
    body: UserCreate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: UserService = Depends(_service),
):
    """Create a new user, or auto-link an existing one to this condominium."""
    user, was_existing = await svc.create_user(body, cid)
    message = (
        "Usuario existente vinculado al condominio."
        if was_existing
        else "Usuario creado exitosamente."
    )
    return success(
        UserCreateResponse(
            user=UserOut.model_validate(user),
            was_existing=was_existing,
            message=message,
        ).model_dump()
    )


@router.post("/{user_id}/restore", dependencies=[Depends(require_super_admin_user)])
async def restore_user(
    user_id: UUID,
    svc: UserService = Depends(_service),
):
    """Restaurar un usuario soft-deleted (solo super_admin)."""
    user = await svc.restore_user(user_id)
    return success(UserOut.model_validate(user).model_dump())


@router.patch("/me")
async def update_my_profile(
    body: UserUpdate,
    current_user=Depends(get_current_user),
    svc: UserService = Depends(_service),
):
    """Self-service: a user updates their own profile fields."""
    user = await svc.update_user(current_user.id, body)
    return success(UserOut.model_validate(user).model_dump())


@router.patch("/{user_id}", dependencies=[Depends(require_authenticated)])
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    current_user=Depends(get_current_user),
    role: str = Depends(get_current_role),
    svc: UserService = Depends(_service),
):
    """Update another user's profile.

    Only the user themselves or super_admin can edit a user's personal data.
    Admins of a condo cannot edit other users' personal info to avoid
    cross-condo conflicts.
    """
    if user_id != current_user.id and role != "super_admin":
        raise ForbiddenError(
            "Solo el propio usuario o super_admin pueden editar este perfil"
        )
    user = await svc.update_user(user_id, body)
    return success(UserOut.model_validate(user).model_dump())


# ── Devices ───────────────────────────────────────────────────────────────


@router.post("/me/devices", status_code=201)
async def register_device(
    body: UserDeviceCreate,
    current_user=Depends(get_current_user),
    svc: UserService = Depends(_service),
):
    device = await svc.register_device(current_user.id, body)
    return success(UserDeviceOut.model_validate(device).model_dump())


@router.get("/me/devices")
async def list_my_devices(
    current_user=Depends(get_current_user),
    svc: UserService = Depends(_service),
):
    devices = await svc.list_devices(current_user.id)
    return success([UserDeviceOut.model_validate(d).model_dump() for d in devices])


@router.delete("/me/devices/{device_id}")
async def deactivate_device(
    device_id: int,
    current_user=Depends(get_current_user),
    svc: UserService = Depends(_service),
):
    await svc.deactivate_device(device_id, current_user.id)
    return success({"message": "Dispositivo desactivado"})
