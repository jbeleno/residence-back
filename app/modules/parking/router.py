"""Parking router."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    get_current_condominium_id,
    require_admin,
    require_admin_or_guard,
    require_authenticated,
)
from app.core.responses import success
from app.modules.parking.repository import ParkingRepository
from app.modules.parking.service import ParkingService
from app.schemas.parking import (
    ParkingSpaceCreate,
    ParkingSpaceUpdate,
    VehicleCreate,
    VehicleUpdate,
    VisitorParkingCreate,
    VisitorParkingExit,
)

router = APIRouter(prefix="/parking", tags=["Parqueaderos"])


def _service(db: AsyncSession = Depends(get_db)) -> ParkingService:
    return ParkingService(ParkingRepository(db))


# ── Spaces ────────────────────────────────────────────────────────────────


@router.get("/spaces", dependencies=[Depends(require_authenticated)])
async def list_parking_spaces(
    cid: UUID = Depends(get_current_condominium_id),
    type_id: int | None = None,
    svc: ParkingService = Depends(_service),
):
    return success(await svc.list_spaces(cid, type_id))


@router.post("/spaces", dependencies=[Depends(require_admin)], status_code=201)
async def create_parking_space(
    body: ParkingSpaceCreate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: ParkingService = Depends(_service),
):
    return success(await svc.create_space(body, cid))


@router.patch("/spaces/{space_id}", dependencies=[Depends(require_admin)])
async def update_parking_space(
    space_id: int,
    body: ParkingSpaceUpdate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: ParkingService = Depends(_service),
):
    return success(await svc.update_space(space_id, body, cid))


# ── Vehicles ──────────────────────────────────────────────────────────────


@router.get("/vehicles", dependencies=[Depends(require_authenticated)])
async def list_vehicles(
    cid: UUID = Depends(get_current_condominium_id),
    property_id: UUID | None = None,
    svc: ParkingService = Depends(_service),
):
    return success(await svc.list_vehicles(cid, property_id))


@router.post("/vehicles", dependencies=[Depends(require_authenticated)], status_code=201)
async def create_vehicle(
    body: VehicleCreate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: ParkingService = Depends(_service),
):
    return success(await svc.create_vehicle(body, cid))


@router.patch("/vehicles/{vehicle_id}", dependencies=[Depends(require_authenticated)])
async def update_vehicle(
    vehicle_id: int,
    body: VehicleUpdate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: ParkingService = Depends(_service),
):
    return success(await svc.update_vehicle(vehicle_id, body, cid))


# ── Visitor Parking ───────────────────────────────────────────────────────


@router.get("/visitor-parking", dependencies=[Depends(require_admin_or_guard)])
async def list_visitor_parking(
    cid: UUID = Depends(get_current_condominium_id),
    active_only: bool = True,
    svc: ParkingService = Depends(_service),
):
    return success(await svc.list_visitor_parking(cid, active_only))


@router.post("/visitor-parking", dependencies=[Depends(require_admin_or_guard)], status_code=201)
async def register_visitor_parking_entry(
    body: VisitorParkingCreate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: ParkingService = Depends(_service),
):
    return success(await svc.register_entry(body, cid))


@router.post("/visitor-parking/{vp_id}/exit", dependencies=[Depends(require_admin_or_guard)])
async def register_visitor_parking_exit(
    vp_id: int,
    body: VisitorParkingExit,
    svc: ParkingService = Depends(_service),
):
    return success(await svc.register_exit(vp_id, body))
