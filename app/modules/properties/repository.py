"""Property repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.core import Property, UserProperty


class PropertyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_by_condo(
        self, cid: UUID, *, is_short_rent: bool | None = None, offset: int = 0, limit: int = 50
    ) -> list[Property]:
        stmt = (
            select(Property)
            .options(selectinload(Property.property_type))
            .where(Property.condominium_id == cid, Property.deleted_at.is_(None))
        )
        if is_short_rent is not None:
            stmt = stmt.where(Property.is_short_rent == is_short_rent)
        stmt = stmt.order_by(Property.block, Property.number).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, property_id: UUID, cid: UUID) -> Property | None:
        result = await self._db.execute(
            select(Property)
            .options(selectinload(Property.property_type))
            .where(
                Property.id == property_id,
                Property.condominium_id == cid,
                Property.deleted_at.is_(None),
            )
        )
        return result.scalars().first()

    async def create(self, cid: UUID, data: dict) -> Property:
        prop = Property(condominium_id=cid, **data)
        self._db.add(prop)
        await self._db.commit()
        await self._db.refresh(prop)
        return prop

    async def update(self, prop: Property, data: dict) -> Property:
        for k, v in data.items():
            setattr(prop, k, v)
        await self._db.commit()
        await self._db.refresh(prop)
        return prop

    # ── User-Property assignments ─────────────────────────────────────────

    async def list_residents(
        self, property_id: UUID, *, active_only: bool = True
    ) -> list[UserProperty]:
        stmt = (
            select(UserProperty)
            .options(
                selectinload(UserProperty.relation_type),
                selectinload(UserProperty.user),
            )
            .where(UserProperty.property_id == property_id)
        )
        if active_only:
            stmt = stmt.where(UserProperty.is_active.is_(True))
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def create_assignment(self, data: dict) -> UserProperty:
        up = UserProperty(**data)
        self._db.add(up)
        await self._db.commit()
        # Re-fetch with eager-loaded relationships
        result = await self._db.execute(
            select(UserProperty)
            .options(
                selectinload(UserProperty.relation_type),
                selectinload(UserProperty.user),
            )
            .where(UserProperty.id == up.id)
        )
        return result.scalars().first()  # type: ignore[return-value]

    async def get_assignment_by_id(self, aid: int) -> UserProperty | None:
        result = await self._db.execute(
            select(UserProperty)
            .options(
                selectinload(UserProperty.relation_type),
                selectinload(UserProperty.user),
            )
            .where(UserProperty.id == aid)
        )
        return result.scalars().first()

    async def update_assignment(self, up: UserProperty, data: dict) -> UserProperty:
        for k, v in data.items():
            setattr(up, k, v)
        await self._db.commit()
        await self._db.refresh(up)
        return up

    async def get_property_any_condo(self, property_id: UUID) -> Property | None:
        """Fetch a property regardless of condominium (for cross-condo transfers)."""
        result = await self._db.execute(
            select(Property)
            .options(selectinload(Property.property_type))
            .where(Property.id == property_id, Property.deleted_at.is_(None))
        )
        return result.scalars().first()

    async def get_property_including_deleted(self, property_id: UUID) -> Property | None:
        result = await self._db.execute(
            select(Property)
            .options(selectinload(Property.property_type))
            .where(Property.id == property_id)
        )
        return result.scalars().first()

    async def restore(self, prop: Property) -> Property:
        prop.deleted_at = None
        prop.is_active = True
        await self._db.commit()
        await self._db.refresh(prop)
        return prop
