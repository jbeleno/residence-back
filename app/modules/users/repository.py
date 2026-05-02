"""User repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Property, Role, User, UserCondominiumRole, UserDevice, UserProperty


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_by_condominium(self, cid: UUID, *, offset: int = 0, limit: int = 50) -> list[User]:
        sub = (
            select(UserCondominiumRole.user_id)
            .where(
                UserCondominiumRole.condominium_id == cid,
                UserCondominiumRole.is_active.is_(True),
            )
            .subquery()
        )
        stmt = (
            select(User)
            .where(User.id.in_(select(sub.c.user_id)), User.deleted_at.is_(None))
            .offset(offset)
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        return result.scalars().first()

    async def get_by_id_including_deleted(self, user_id: UUID) -> User | None:
        result = await self._db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalars().first()

    async def restore(self, user: User) -> User:
        user.deleted_at = None
        user.is_active = True
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()

    async def get_role_by_name(self, role_name: str) -> Role | None:
        result = await self._db.execute(
            select(Role).where(Role.role_name == role_name)
        )
        return result.scalars().first()

    async def create_user(self, user: User) -> User:
        self._db.add(user)
        await self._db.flush()
        return user

    async def create_ucr(self, ucr: UserCondominiumRole) -> None:
        self._db.add(ucr)

    async def get_ucr(self, user_id: UUID, cid: UUID) -> UserCondominiumRole | None:
        """Check if user already has a role in the given condominium."""
        result = await self._db.execute(
            select(UserCondominiumRole).where(
                UserCondominiumRole.user_id == user_id,
                UserCondominiumRole.condominium_id == cid,
            )
        )
        return result.scalars().first()

    async def get_active_ucr(self, user_id: UUID, cid: UUID) -> UserCondominiumRole | None:
        """Active link between a user and a condominium."""
        result = await self._db.execute(
            select(UserCondominiumRole).where(
                UserCondominiumRole.user_id == user_id,
                UserCondominiumRole.condominium_id == cid,
                UserCondominiumRole.is_active.is_(True),
            )
        )
        return result.scalars().first()

    async def deactivate_ucr(self, ucr: UserCondominiumRole) -> None:
        ucr.is_active = False

    async def deactivate_user_properties_in_condo(
        self, user_id: UUID, cid: UUID,
    ) -> int:
        """Deactivate every active UserProperty of the user that lives in
        properties of the given condominium. Returns how many were touched."""
        from datetime import date

        sub = (
            select(UserProperty.id)
            .join(Property, UserProperty.property_id == Property.id)
            .where(
                UserProperty.user_id == user_id,
                UserProperty.is_active.is_(True),
                Property.condominium_id == cid,
            )
        )
        result = await self._db.execute(sub)
        ids = [row[0] for row in result.all()]
        if not ids:
            return 0
        rows = await self._db.execute(
            select(UserProperty).where(UserProperty.id.in_(ids))
        )
        today = date.today()
        for up in rows.scalars().all():
            up.is_active = False
            up.end_date = today
        return len(ids)

    async def update(self, user: User, data: dict) -> User:
        for key, val in data.items():
            setattr(user, key, val)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def commit_and_refresh(self, obj) -> None:
        await self._db.commit()
        await self._db.refresh(obj)

    # ── Devices ───────────────────────────────────────────────────────────

    async def get_device(self, user_id: UUID, token: str) -> UserDevice | None:
        result = await self._db.execute(
            select(UserDevice).where(
                UserDevice.user_id == user_id,
                UserDevice.device_token == token,
            )
        )
        return result.scalars().first()

    async def list_devices(self, user_id: UUID) -> list[UserDevice]:
        result = await self._db.execute(
            select(UserDevice).where(
                UserDevice.user_id == user_id,
                UserDevice.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def get_device_by_id(self, device_id: int, user_id: UUID) -> UserDevice | None:
        result = await self._db.execute(
            select(UserDevice).where(
                UserDevice.id == device_id,
                UserDevice.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def add_device(self, device: UserDevice) -> UserDevice:
        self._db.add(device)
        await self._db.commit()
        await self._db.refresh(device)
        return device
