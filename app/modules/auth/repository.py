"""Auth repository – pure DB queries."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.core import Condominium, Property, Role, User, UserCondominiumRole, UserProperty
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

    async def is_super_admin(self, user_id: UUID) -> bool:
        """Return True if the user has a super_admin role in *any* condominium."""
        stmt = (
            select(UserCondominiumRole.id)
            .join(Role, UserCondominiumRole.role_id == Role.id)
            .where(
                UserCondominiumRole.user_id == user_id,
                UserCondominiumRole.is_active.is_(True),
                Role.role_name == "super_admin",
            )
            .limit(1)
        )
        result = await self._db.execute(stmt)
        return result.first() is not None

    async def get_condominium_by_id(self, condominium_id: UUID) -> Condominium | None:
        stmt = select(Condominium).where(
            Condominium.id == condominium_id,
            Condominium.deleted_at.is_(None),
        )
        result = await self._db.execute(stmt)
        return result.scalars().first()

    async def list_condominiums(self) -> list[Condominium]:
        stmt = select(Condominium).where(Condominium.deleted_at.is_(None)).order_by(Condominium.name)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

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

    async def create_pin(
        self,
        user_id: UUID,
        pin_code: str,
        pin_type: str,
        expires_at: datetime,
        payload: str | None = None,
    ) -> EmailPin:
        pin = EmailPin(
            user_id=user_id,
            pin_code=pin_code,
            pin_type=pin_type,
            expires_at=expires_at,
            payload=payload,
        )
        self._db.add(pin)
        await self._db.flush()
        return pin

    async def get_valid_pin(self, user_id: UUID, pin_code: str, pin_type: str) -> EmailPin | None:
        now = datetime.utcnow()
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

    async def create_user(
        self, full_name: str, email: str, password: str, phone: str | None = None,
    ) -> User:
        user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            phone=phone,
        )
        self._db.add(user)
        await self._db.flush()
        return user

    async def assign_condominium_role(
        self, user_id: UUID, condominium_id: UUID, role_id: int = 4,
    ) -> None:
        """Assign user to a condominium with a role (default: residente, role_id=4)."""
        ucr = UserCondominiumRole(
            user_id=user_id,
            condominium_id=condominium_id,
            role_id=role_id,
        )
        self._db.add(ucr)
        await self._db.flush()

    async def mark_pin_used(self, pin: EmailPin) -> None:
        pin.used = True

    async def get_user_properties(self, user_id: UUID) -> list[tuple[UserProperty, Property]]:
        stmt = (
            select(UserProperty, Property)
            .join(Property, UserProperty.property_id == Property.id)
            .where(
                UserProperty.user_id == user_id,
                UserProperty.is_active.is_(True),
                Property.deleted_at.is_(None),
            )
        )
        result = await self._db.execute(stmt)
        return result.all()  # type: ignore[return-value]

    async def save(self) -> None:
        await self._db.commit()
