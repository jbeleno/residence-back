"""Parking service."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from uuid import UUID

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.visitor import VisitorParking
from app.modules.parking.repository import ParkingRepository
from app.schemas.parking import (
    ParkingSpaceCreate,
    ParkingSpaceOut,
    ParkingSpaceUpdate,
    VehicleCreate,
    VehicleOut,
    VehicleUpdate,
    VisitorParkingCreate,
    VisitorParkingExit,
    VisitorParkingOut,
)


class ParkingService:
    def __init__(self, repo: ParkingRepository) -> None:
        self._repo = repo

    # ── Spaces ────────────────────────────────────────────────────────────

    async def list_spaces(self, cid: UUID, type_id: int | None):
        spaces = await self._repo.list_spaces(cid, type_id=type_id)
        return [self._space_out(s) for s in spaces]

    async def create_space(self, body: ParkingSpaceCreate, cid: UUID):
        s = await self._repo.create_space(cid, body.model_dump())
        return self._space_out(s)

    async def update_space(self, space_id: int, body: ParkingSpaceUpdate, cid: UUID):
        s = await self._repo.get_space(space_id, cid)
        if not s:
            raise NotFoundError("Parqueadero no encontrado")
        s = await self._repo.update_space(s, body.model_dump(exclude_unset=True))
        return self._space_out(s)

    # ── Vehicles ──────────────────────────────────────────────────────────

    async def list_vehicles(self, cid: UUID, property_id: UUID | None):
        vehicles = await self._repo.list_vehicles(cid, property_id=property_id)
        return [self._vehicle_out(v) for v in vehicles]

    async def create_vehicle(self, body: VehicleCreate, cid: UUID):
        v = await self._repo.create_vehicle(cid, body.model_dump())
        return self._vehicle_out(v)

    async def update_vehicle(self, vehicle_id: int, body: VehicleUpdate, cid: UUID):
        v = await self._repo.get_vehicle(vehicle_id, cid)
        if not v:
            raise NotFoundError("Vehículo no encontrado")
        v = await self._repo.update_vehicle(v, body.model_dump(exclude_unset=True))
        return self._vehicle_out(v)

    # ── Visitor Parking ───────────────────────────────────────────────────

    async def list_visitor_parking(self, cid: UUID, active_only: bool):
        entries = await self._repo.list_visitor_parking(cid, active_only=active_only)
        return [self._vp_out(vp) for vp in entries]

    async def register_entry(self, body: VisitorParkingCreate, cid: UUID):
        rate = body.hourly_rate
        if rate == 0:
            condo = await self._repo.get_condominium(cid)
            if condo:
                rate = float(condo.visitor_parking_hourly_rate or 0)

        vp = VisitorParking(
            visitor_log_id=body.visitor_log_id,
            parking_space_id=body.parking_space_id,
            hourly_rate=rate,
        )
        vp = await self._repo.create_visitor_parking(vp)
        return self._vp_out(vp)

    async def register_exit(self, vp_id: int, body: VisitorParkingExit):
        vp = await self._repo.get_visitor_parking(vp_id)
        if not vp:
            raise NotFoundError("Registro de parqueo no encontrado")
        if vp.exit_time:
            raise BadRequestError("Ya se registró la salida")

        vp.exit_time = datetime.now(timezone.utc)
        hours = (vp.exit_time - vp.entry_time).total_seconds() / 3600
        vp.total_cost = math.ceil(hours) * float(vp.hourly_rate)
        vp.is_paid = body.is_paid
        await self._repo.commit()
        await self._repo.refresh(vp)
        return self._vp_out(vp)

    # ── Mappers ───────────────────────────────────────────────────────────

    @staticmethod
    def _space_out(s) -> dict:
        return ParkingSpaceOut(
            id=s.id,
            condominium_id=s.condominium_id,
            space_number=s.space_number,
            parking_space_type_id=s.parking_space_type_id,
            parking_type_name=s.parking_type.name if s.parking_type else None,
            property_id=s.property_id,
            is_active=s.is_active,
            created_at=s.created_at,
        ).model_dump()

    @staticmethod
    def _vehicle_out(v) -> dict:
        return VehicleOut(
            id=v.id,
            condominium_id=v.condominium_id,
            property_id=v.property_id,
            license_plate=v.license_plate,
            brand=v.brand,
            model=v.model,
            color=v.color,
            vehicle_type_id=v.vehicle_type_id,
            vehicle_type_name=v.vehicle_type.name if v.vehicle_type else None,
            is_active=v.is_active,
            created_at=v.created_at,
        ).model_dump()

    @staticmethod
    def _vp_out(vp) -> dict:
        return VisitorParkingOut(
            id=vp.id,
            visitor_log_id=vp.visitor_log_id,
            parking_space_id=vp.parking_space_id,
            space_number=vp.parking_space.space_number if vp.parking_space else None,
            entry_time=vp.entry_time,
            exit_time=vp.exit_time,
            hourly_rate=float(vp.hourly_rate),
            total_cost=float(vp.total_cost) if vp.total_cost else None,
            is_paid=vp.is_paid,
            created_at=vp.created_at,
        ).model_dump()
