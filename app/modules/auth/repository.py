"""Auth repository – pure DB queries."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Condominium, Role, User, UserCondominiumRole
from app.models.email_pin import EmailPin


class AuthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self._db.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        return result.scalars().first()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        result = await self._db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        return result.scalars().first()

    async def get_user_condominium_roles(
        self, user_id: UUID
    ) -> list[tuple[UserCondominiumRole, Condominium, Role]]:
        stmt = (
            select(UserCondominiumRole, Condominium, Role)
            .join(Condominium, UserCondominiumRole.condominium_id == Condominium.id)
            .join(Role, UserCondominiumRole.role_id == Role.id)
            .where(
                UserCondominiumRole.user_id == user_id,
                UserCondominiumRole.is_active.is_(True),
                Condominium.deleted_at.is_(None),
            )
        )
        result = await self._db.execute(stmt)
        return result.all()  # type: ignore[return-value]

    async def get_user_role_in_condominium(
        self, user_id: UUID, condominium_id: UUID
    ) -> tuple[UserCondominiumRole, Role] | None:
        stmt = (
            select(UserCondominiumRole, Role)
            .join(Role, UserCondominiumRole.role_id == Role.id)
            .where(
                UserCondominiumRole.user_id == user_id,
                UserCondominiumRole.condominium_id == condominium_id,
                UserCondominiumRole.is_active.is_(True),
            )
        )
        result = await self._db.execute(stmt)
        return result.first()  # type: ignore[return-value]

    # ── PIN operations ────────────────────────────────────────────────────

    async def invalidate_existing_pins(self, user_id: UUID, pin_type: str) -> None:
        """Mark all unused PINs of this type as used (invalidate)."""
        await self._db.execute(
            update(EmailPin)
            .where(
                EmailPin.user_id == user_id,
                EmailPin.pin_type == pin_type,
                EmailPin.used.is_(False),
            )
            .values(used=True)
        )

    async def create_pin(self, user_id: UUID, pin_code: str, pin_type: str, expires_at: datetime) -> EmailPin:
        pin = EmailPin(
            user_id=user_id,
            pin_code=pin_code,
            pin_type=pin_type,
            expires_at=expires_at,
        )
        self._db.add(pin)
        await self._db.flush()
        return pin

    async def get_valid_pin(self, user_id: UUID, pin_code: str, pin_type: str) -> EmailPin | None:
        now = datetime.now(timezone.utc)
        result = await self._db.execute(
            select(EmailPin).where(
                EmailPin.user_id == user_id,
                EmailPin.pin_code == pin_code,
                EmailPin.pin_type == pin_type,
                EmailPin.used.is_(False),
                EmailPin.expires_at > now,
            )
        )
        return result.scalars().first()

    async def mark_pin_used(self, pin: EmailPin) -> None:
        pin.used = True

    async def save(self) -> None:
        await self._db.commit()
