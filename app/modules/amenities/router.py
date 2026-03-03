"""Amenity router."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    get_current_condominium_id,
    get_current_user,
    require_admin,
    require_authenticated,
)
from app.core.responses import success
from app.modules.amenities.repository import AmenityRepository
from app.modules.amenities.service import AmenityService
from app.schemas.amenity import AmenityCreate, AmenityUpdate, BookingCreate, BookingUpdateStatus

router = APIRouter(prefix="/amenities", tags=["Zonas Sociales"])


def _service(db: AsyncSession = Depends(get_db)) -> AmenityService:
    return AmenityService(AmenityRepository(db))


@router.get("/", dependencies=[Depends(require_authenticated)])
async def list_amenities(
    cid: UUID = Depends(get_current_condominium_id),
    active_only: bool = True,
    svc: AmenityService = Depends(_service),
):
    return success(await svc.list_amenities(cid, active_only))


@router.get("/{amenity_id}", dependencies=[Depends(require_authenticated)])
async def get_amenity(
    amenity_id: int,
    cid: UUID = Depends(get_current_condominium_id),
    svc: AmenityService = Depends(_service),
):
    return success(await svc.get_amenity(amenity_id, cid))


@router.post("/", dependencies=[Depends(require_admin)], status_code=201)
async def create_amenity(
    body: AmenityCreate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: AmenityService = Depends(_service),
):
    return success(await svc.create_amenity(body, cid))


@router.patch("/{amenity_id}", dependencies=[Depends(require_admin)])
async def update_amenity(
    amenity_id: int,
    body: AmenityUpdate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: AmenityService = Depends(_service),
):
    return success(await svc.update_amenity(amenity_id, body, cid))


# ── Bookings ──────────────────────────────────────────────────────────────


@router.get("/bookings/all", dependencies=[Depends(require_authenticated)])
async def list_bookings(
    cid: UUID = Depends(get_current_condominium_id),
    amenity_id: int | None = None,
    status_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    svc: AmenityService = Depends(_service),
):
    return success(await svc.list_bookings(cid, amenity_id, status_id, skip, limit))


@router.post("/bookings", status_code=201)
async def create_booking(
    body: BookingCreate,
    cid: UUID = Depends(get_current_condominium_id),
    current_user=Depends(get_current_user),
    svc: AmenityService = Depends(_service),
):
    return success(await svc.create_booking(body, cid, current_user.id))


@router.patch("/bookings/{booking_id}/status", dependencies=[Depends(require_admin)])
async def update_booking_status(
    booking_id: UUID,
    body: BookingUpdateStatus,
    cid: UUID = Depends(get_current_condominium_id),
    current_user=Depends(get_current_user),
    svc: AmenityService = Depends(_service),
):
    return success(await svc.update_booking_status(booking_id, body, cid, current_user.id))
