"""User service."""

from __future__ import annotations

from uuid import UUID

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.core import User, UserCondominiumRole, UserDevice
from app.modules.users.repository import UserRepository
from app.schemas.user import UserCreate, UserDeviceCreate, UserUpdate


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def list_users(self, cid: UUID, offset: int, limit: int):
        return await self._repo.list_by_condominium(cid, offset=offset, limit=limit)

    async def get_user(self, user_id: UUID):
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado")
        return user

    async def create_user(self, body: UserCreate, cid: UUID):
        # Duplicate check
        existing = await self._repo.get_by_email(body.email)
        if existing:
            raise ConflictError("El email ya está registrado")

        user_data = body.model_dump(exclude={"password", "role_id", "condominium_id"})
        user = User(**user_data, password_hash=hash_password(body.password))
        user = await self._repo.create_user(user)

        # Assign role
        role_id = body.role_id or 4  # default: residente
        target_cid = body.condominium_id or cid
        ucr = UserCondominiumRole(user_id=user.id, condominium_id=target_cid, role_id=role_id)
        await self._repo.create_ucr(ucr)
        await self._repo.commit_and_refresh(user)
        return user

    async def update_user(self, user_id: UUID, body: UserUpdate):
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado")
        return await self._repo.update(user, body.model_dump(exclude_unset=True))

    # ── Devices ───────────────────────────────────────────────────────────

    async def register_device(self, user_id: UUID, body: UserDeviceCreate):
        existing = await self._repo.get_device(user_id, body.device_token)
        if existing:
            existing.is_active = True
            existing.device_type = body.device_type
            existing.device_name = body.device_name
            await self._repo.commit_and_refresh(existing)
            return existing

        device = UserDevice(user_id=user_id, **body.model_dump())
        return await self._repo.add_device(device)

    async def list_devices(self, user_id: UUID):
        return await self._repo.list_devices(user_id)

    async def deactivate_device(self, device_id: int, user_id: UUID):
        device = await self._repo.get_device_by_id(device_id, user_id)
        if device is None:
            raise NotFoundError("Dispositivo no encontrado")
        device.is_active = False
        await self._repo.commit_and_refresh(device)
