"""Visitor service."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.visitor import VisitorLog
from app.modules.visitors.repository import VisitorRepository
from app.schemas.visitor import VisitorLogCreate, VisitorLogOut


class VisitorService:
    def __init__(self, repo: VisitorRepository) -> None:
        self._repo = repo

    async def list_visitors(self, cid, active_only, property_id, offset, limit):
        visitors = await self._repo.list_visitors(
            cid, active_only=active_only, property_id=property_id, offset=offset, limit=limit,
        )
        return [self._out(v) for v in visitors]

    async def list_active(self, cid: UUID):
        visitors = await self._repo.list_visitors(cid, active_only=True)
        return [self._out(v) for v in visitors]

    async def get_visitor(self, visitor_id: UUID, cid: UUID):
        v = await self._repo.get_by_id(visitor_id, cid)
        if not v:
            raise NotFoundError("Registro de visitante no encontrado")
        return self._out(v)

    async def register_entry(self, body: VisitorLogCreate, cid: UUID, user_id: UUID):
        visitor = VisitorLog(
            condominium_id=cid,
            registered_by=user_id,
            **body.model_dump(),
        )
        visitor = await self._repo.create(visitor)
        return self._out(visitor)

    async def register_exit(self, visitor_id: UUID, cid: UUID):
        v = await self._repo.get_by_id(visitor_id, cid)
        if not v:
            raise NotFoundError("Visitante no encontrado")
        if v.exit_time:
            raise BadRequestError("El visitante ya registró salida")
        v.exit_time = datetime.utcnow()
        await self._repo.commit()
        await self._repo.refresh(v)
        return self._out(v)

    @staticmethod
    def _out(v: VisitorLog) -> dict:
        return VisitorLogOut(
            id=v.id,
            condominium_id=v.condominium_id,
            property_id=v.property_id,
            property_number=v.property.number if v.property else None,
            visitor_name=v.visitor_name,
            document_type_id=v.document_type_id,
            document_type_name=v.document_type.name if v.document_type else None,
            document_number=v.document_number,
            is_guest=v.is_guest,
            vehicle_plate=v.vehicle_plate,
            authorized_by=v.authorized_by,
            authorized_by_name=v.authorized_user.full_name if v.authorized_user else None,
            registered_by=v.registered_by,
            entry_time=v.entry_time,
            exit_time=v.exit_time,
            notes=v.notes,
            created_at=v.created_at,
        ).model_dump()
