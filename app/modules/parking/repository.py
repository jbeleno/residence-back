"""Parking repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.core import Condominium
from app.models.visitor import ParkingSpace, Vehicle, VisitorParking


class ParkingRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Spaces ────────────────────────────────────────────────────────────

    async def list_spaces(self, cid: UUID, *, type_id: int | None = None) -> list[ParkingSpace]:
        stmt = (
            select(ParkingSpace)
            .options(selectinload(ParkingSpace.parking_type))
            .where(ParkingSpace.condominium_id == cid, ParkingSpace.is_active.is_(True))
        )
        if type_id:
            stmt = stmt.where(ParkingSpace.parking_space_type_id == type_id)
        stmt = stmt.order_by(ParkingSpace.space_number)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_space(self, space_id: int, cid: UUID) -> ParkingSpace | None:
        result = await self._db.execute(
            select(ParkingSpace)
            .options(selectinload(ParkingSpace.parking_type))
            .where(ParkingSpace.id == space_id, ParkingSpace.condominium_id == cid)
        )
        return result.scalars().first()

    async def create_space(self, cid: UUID, data: dict) -> ParkingSpace:
        s = ParkingSpace(condominium_id=cid, **data)
        self._db.add(s)
        await self._db.commit()
        await self._db.refresh(s)
        return s

    async def update_space(self, space: ParkingSpace, data: dict) -> ParkingSpace:
        for k, v in data.items():
            setattr(space, k, v)
        await self._db.commit()
        await self._db.refresh(space)
        return space

    # ── Vehicles ──────────────────────────────────────────────────────────

    async def list_vehicles(self, cid: UUID, *, property_id: UUID | None = None) -> list[Vehicle]:
        stmt = (
            select(Vehicle)
            .options(selectinload(Vehicle.vehicle_type))
            .where(Vehicle.condominium_id == cid, Vehicle.is_active.is_(True))
        )
        if property_id:
            stmt = stmt.where(Vehicle.property_id == property_id)
        stmt = stmt.order_by(Vehicle.license_plate)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_vehicle(self, vehicle_id: int, cid: UUID) -> Vehicle | None:
        result = await self._db.execute(
            select(Vehicle)
            .options(selectinload(Vehicle.vehicle_type))
            .where(Vehicle.id == vehicle_id, Vehicle.condominium_id == cid)
        )
        return result.scalars().first()

    async def create_vehicle(self, cid: UUID, data: dict) -> Vehicle:
        v = Vehicle(condominium_id=cid, **data)
        self._db.add(v)
        await self._db.commit()
        await self._db.refresh(v)
        return v

    async def update_vehicle(self, vehicle: Vehicle, data: dict) -> Vehicle:
        for k, v in data.items():
            setattr(vehicle, k, v)
        await self._db.commit()
        await self._db.refresh(vehicle)
        return vehicle

    # ── Visitor Parking ───────────────────────────────────────────────────

    async def list_visitor_parking(self, cid: UUID, *, active_only: bool = True) -> list[VisitorParking]:
        stmt = (
            select(VisitorParking)
            .join(ParkingSpace, VisitorParking.parking_space_id == ParkingSpace.id)
            .options(selectinload(VisitorParking.parking_space))
            .where(ParkingSpace.condominium_id == cid)
        )
        if active_only:
            stmt = stmt.where(VisitorParking.exit_time.is_(None))
        stmt = stmt.order_by(VisitorParking.entry_time.desc())
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_visitor_parking(self, vp_id: int) -> VisitorParking | None:
        result = await self._db.execute(
            select(VisitorParking)
            .options(selectinload(VisitorParking.parking_space))
            .where(VisitorParking.id == vp_id)
        )
        return result.scalars().first()

    async def create_visitor_parking(self, vp: VisitorParking) -> VisitorParking:
        self._db.add(vp)
        await self._db.commit()
        await self._db.refresh(vp)
        return vp

    async def get_condominium(self, cid: UUID) -> Condominium | None:
        result = await self._db.execute(select(Condominium).where(Condominium.id == cid))
        return result.scalars().first()

    async def commit(self) -> None:
        await self._db.commit()

    async def refresh(self, obj) -> None:
        await self._db.refresh(obj)
