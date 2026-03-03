"""Amenity repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.amenity import Amenity, AmenityBooking
from app.models.catalog import BookingStatus


class AmenityRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Amenities ─────────────────────────────────────────────────────────

    async def list_amenities(self, cid: UUID, *, active_only: bool = True) -> list[Amenity]:
        stmt = select(Amenity).where(Amenity.condominium_id == cid)
        if active_only:
            stmt = stmt.where(Amenity.is_active.is_(True))
        stmt = stmt.order_by(Amenity.name)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_amenity(self, amenity_id: int, cid: UUID) -> Amenity | None:
        result = await self._db.execute(
            select(Amenity).where(Amenity.id == amenity_id, Amenity.condominium_id == cid)
        )
        return result.scalars().first()

    async def create_amenity(self, cid: UUID, data: dict) -> Amenity:
        a = Amenity(condominium_id=cid, **data)
        self._db.add(a)
        await self._db.commit()
        await self._db.refresh(a)
        return a

    async def update_amenity(self, amenity: Amenity, data: dict) -> Amenity:
        for k, v in data.items():
            setattr(amenity, k, v)
        await self._db.commit()
        await self._db.refresh(amenity)
        return amenity

    # ── Bookings ──────────────────────────────────────────────────────────

    async def list_bookings(
        self,
        cid: UUID,
        *,
        amenity_id: int | None = None,
        status_id: int | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AmenityBooking]:
        stmt = (
            select(AmenityBooking)
            .join(Amenity, AmenityBooking.amenity_id == Amenity.id)
            .options(
                selectinload(AmenityBooking.amenity),
                selectinload(AmenityBooking.user),
                selectinload(AmenityBooking.booking_status),
            )
            .where(Amenity.condominium_id == cid)
        )
        if amenity_id:
            stmt = stmt.where(AmenityBooking.amenity_id == amenity_id)
        if status_id:
            stmt = stmt.where(AmenityBooking.booking_status_id == status_id)
        stmt = stmt.order_by(AmenityBooking.start_time.desc()).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_booking(self, booking_id: UUID, cid: UUID) -> AmenityBooking | None:
        result = await self._db.execute(
            select(AmenityBooking)
            .join(Amenity, AmenityBooking.amenity_id == Amenity.id)
            .options(
                selectinload(AmenityBooking.amenity),
                selectinload(AmenityBooking.user),
                selectinload(AmenityBooking.booking_status),
            )
            .where(AmenityBooking.id == booking_id, Amenity.condominium_id == cid)
        )
        return result.scalars().first()

    async def check_overlap(self, amenity_id: int, start, end) -> AmenityBooking | None:
        result = await self._db.execute(
            select(AmenityBooking).where(
                AmenityBooking.amenity_id == amenity_id,
                AmenityBooking.booking_status_id.in_([1, 2]),
                AmenityBooking.start_time < end,
                AmenityBooking.end_time > start,
            )
        )
        return result.scalars().first()

    async def get_booking_status_by_code(self, code: str) -> BookingStatus | None:
        result = await self._db.execute(
            select(BookingStatus).where(BookingStatus.code == code)
        )
        return result.scalars().first()

    async def get_booking_status_by_id(self, sid: int) -> BookingStatus | None:
        result = await self._db.execute(select(BookingStatus).where(BookingStatus.id == sid))
        return result.scalars().first()

    async def create_booking(self, booking: AmenityBooking) -> AmenityBooking:
        self._db.add(booking)
        await self._db.commit()
        await self._db.refresh(booking)
        return booking

    async def commit(self) -> None:
        await self._db.commit()

    async def refresh(self, obj) -> None:
        await self._db.refresh(obj)
