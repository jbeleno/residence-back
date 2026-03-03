"""Amenity service."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.core.enums import BookingStatusEnum
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.amenity import AmenityBooking
from app.modules.amenities.repository import AmenityRepository
from app.schemas.amenity import (
    AmenityCreate,
    AmenityOut,
    AmenityUpdate,
    BookingCreate,
    BookingOut,
    BookingUpdateStatus,
)


class AmenityService:
    def __init__(self, repo: AmenityRepository) -> None:
        self._repo = repo

    # ── Amenities ─────────────────────────────────────────────────────────

    async def list_amenities(self, cid: UUID, active_only: bool):
        items = await self._repo.list_amenities(cid, active_only=active_only)
        return [AmenityOut.model_validate(a).model_dump() for a in items]

    async def get_amenity(self, amenity_id: int, cid: UUID):
        a = await self._repo.get_amenity(amenity_id, cid)
        if not a:
            raise NotFoundError("Amenidad no encontrada")
        return AmenityOut.model_validate(a).model_dump()

    async def create_amenity(self, body: AmenityCreate, cid: UUID):
        a = await self._repo.create_amenity(cid, body.model_dump())
        return AmenityOut.model_validate(a).model_dump()

    async def update_amenity(self, amenity_id: int, body: AmenityUpdate, cid: UUID):
        a = await self._repo.get_amenity(amenity_id, cid)
        if not a:
            raise NotFoundError("Amenidad no encontrada")
        a = await self._repo.update_amenity(a, body.model_dump(exclude_unset=True))
        return AmenityOut.model_validate(a).model_dump()

    # ── Bookings ──────────────────────────────────────────────────────────

    async def list_bookings(self, cid, amenity_id, status_id, offset, limit):
        bookings = await self._repo.list_bookings(
            cid, amenity_id=amenity_id, status_id=status_id, offset=offset, limit=limit
        )
        return [self._booking_out(b) for b in bookings]

    async def create_booking(self, body: BookingCreate, cid: UUID, user_id: UUID):
        amenity = await self._repo.get_amenity(body.amenity_id, cid)
        if not amenity:
            raise NotFoundError("Amenidad no encontrada")
        if not amenity.is_active:
            raise BadRequestError("Amenidad no disponible")

        overlap = await self._repo.check_overlap(body.amenity_id, body.start_time, body.end_time)
        if overlap:
            raise ConflictError("Horario no disponible, hay cruce con otra reserva")

        hours = (body.end_time - body.start_time).total_seconds() / 3600
        total_cost = float(amenity.hourly_cost) * hours

        pending = await self._repo.get_booking_status_by_code("pendiente")

        booking = AmenityBooking(
            amenity_id=body.amenity_id,
            property_id=body.property_id,
            booked_by=user_id,
            booking_status_id=pending.id if pending else BookingStatusEnum.PENDIENTE,
            start_time=body.start_time,
            end_time=body.end_time,
            total_cost=total_cost,
            notes=body.notes,
        )
        booking = await self._repo.create_booking(booking)
        return self._booking_out(booking)

    async def update_booking_status(
        self, booking_id: UUID, body: BookingUpdateStatus, cid: UUID, user_id: UUID
    ):
        booking = await self._repo.get_booking(booking_id, cid)
        if not booking:
            raise NotFoundError("Reserva no encontrada")

        new_status = await self._repo.get_booking_status_by_id(body.booking_status_id)
        if not new_status:
            raise BadRequestError("Estado no válido")

        booking.booking_status_id = body.booking_status_id

        if new_status.code == "aprobada":
            booking.approved_by = user_id
            booking.approved_at = datetime.now(timezone.utc)
        elif new_status.code == "cancelada":
            booking.cancelled_by = user_id
            booking.cancelled_at = datetime.now(timezone.utc)

        await self._repo.commit()
        await self._repo.refresh(booking)
        return self._booking_out(booking)

    @staticmethod
    def _booking_out(b: AmenityBooking) -> dict:
        return BookingOut(
            id=b.id,
            amenity_id=b.amenity_id,
            amenity_name=b.amenity.name if b.amenity else None,
            property_id=b.property_id,
            booked_by=b.booked_by,
            booked_by_name=b.user.full_name if b.user else None,
            booking_status_id=b.booking_status_id,
            booking_status_name=b.booking_status.name if b.booking_status else None,
            start_time=b.start_time,
            end_time=b.end_time,
            total_cost=float(b.total_cost or 0),
            invoice_id=b.invoice_id,
            notes=b.notes,
            approved_by=b.approved_by,
            approved_at=b.approved_at,
            cancelled_at=b.cancelled_at,
            created_at=b.created_at,
        ).model_dump()
