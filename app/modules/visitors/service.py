"""Visitor service."""

from __future__ import annotations

import secrets
import string
from datetime import date, datetime
from uuid import UUID

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.visitor import VisitorLog
from app.modules.visitors.repository import VisitorRepository
from app.schemas.visitor import (
    PublicVisitorPreregister,
    PublicVisitorPreregisterOut,
    ResidentVisitorCreate,
    VisitorLogCreate,
    VisitorLogOut,
)


class VisitorService:
    def __init__(self, repo: VisitorRepository) -> None:
        self._repo = repo

    async def list_visitors(self, cid, active_only, property_id, offset, limit):
        visitors = await self._repo.list_visitors(
            cid, active_only=active_only, property_id=property_id, offset=offset, limit=limit,
        )
        return [self._out(v) for v in visitors]

    async def list_active(self, cid: UUID, *, property_id: UUID | None = None):
        visitors = await self._repo.list_visitors(cid, active_only=True, property_id=property_id)
        return [self._out(v) for v in visitors]

    async def list_pending(self, cid: UUID):
        """List pre-registered visitors (entry_time is NULL)."""
        visitors = await self._repo.list_pending(cid)
        return [self._out(v) for v in visitors]

    async def get_visitor(self, visitor_id: UUID, cid: UUID):
        v = await self._repo.get_by_id(visitor_id, cid)
        if not v:
            raise NotFoundError("Registro de visitante no encontrado")
        return self._out(v)

    async def resident_register_entry(self, body: ResidentVisitorCreate, cid: UUID, user):
        """Resident pre-registers a visitor (no entry_time yet)."""
        user_property_ids = await self._repo.get_user_property_ids_in_condo(user.id, cid)
        if not user_property_ids:
            raise BadRequestError("No tienes una propiedad asignada en este conjunto")

        property_id = next(iter(user_property_ids))
        visitor = VisitorLog(
            condominium_id=cid,
            property_id=property_id,
            registered_by=user.id,
            authorized_by=user.id,
            visitor_name=body.visitor_name,
            document_number=body.document_number,
            vehicle_plate=body.vehicle_plate,
            notes=body.notes,
            is_guest=True,
            # entry_time stays None → pre-registered
        )
        visitor = await self._repo.create(visitor)
        return self._out(visitor)

    @staticmethod
    def _generate_reference_code() -> str:
        today = date.today().strftime("%Y%m%d")
        suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        return f"VIS-{today}-{suffix}"

    async def public_preregister(self, body: PublicVisitorPreregister) -> dict:
        """Public visitor pre-registration (no auth required)."""
        condo = await self._repo.get_condominium(body.condominium_id)
        if not condo:
            raise NotFoundError("Condominio no encontrado o inactivo")

        prop = await self._repo.get_property_by_number(body.condominium_id, body.property_number)
        if not prop:
            raise NotFoundError(
                f"Propiedad '{body.property_number}' no encontrada en este condominio"
            )

        notes_parts = []
        if body.vehicle_type:
            notes_parts.append(f"Tipo vehículo: {body.vehicle_type}")
        if body.reason:
            notes_parts.append(f"Motivo: {body.reason}")

        visitor = VisitorLog(
            condominium_id=body.condominium_id,
            property_id=prop.id,
            visitor_name=body.visitor_name,
            document_type_id=body.document_type_id,
            document_number=body.document_number,
            phone=body.phone,
            reason=body.reason,
            expected_date=body.expected_date,
            expected_time=body.expected_time,
            vehicle_plate=body.vehicle_plate,
            reference_code=self._generate_reference_code(),
            notes="; ".join(notes_parts) if notes_parts else None,
            is_guest=True,
        )
        visitor = await self._repo.create(visitor)
        return PublicVisitorPreregisterOut(
            visitor_id=visitor.id,
            reference_code=visitor.reference_code,
        ).model_dump()

    async def register_entry(self, body: VisitorLogCreate, cid: UUID, user_id: UUID):
        """Admin/guard registers a visitor with immediate entry."""
        visitor = VisitorLog(
            condominium_id=cid,
            registered_by=user_id,
            entry_time=datetime.utcnow(),
            **body.model_dump(),
        )
        visitor = await self._repo.create(visitor)
        return self._out(visitor)

    async def confirm_entry(self, visitor_id: UUID, cid: UUID):
        """Admin/guard confirms a pre-registered visitor has arrived."""
        v = await self._repo.get_by_id(visitor_id, cid)
        if not v:
            raise NotFoundError("Visitante no encontrado")
        if v.entry_time:
            raise BadRequestError("Ya se confirmó la entrada de este visitante")
        v.entry_time = datetime.utcnow()
        await self._repo.commit()
        await self._repo.refresh(v)
        return self._out(v)

    async def resident_register_exit(self, visitor_id: UUID, cid: UUID, user):
        """Resident marks their own visitor as exited."""
        v = await self._repo.get_by_id(visitor_id, cid)
        if not v:
            raise NotFoundError("Visitante no encontrado")
        user_property_ids = await self._repo.get_user_property_ids_in_condo(user.id, cid)
        if v.property_id not in user_property_ids:
            raise BadRequestError("Solo puedes registrar salida de tus propios visitantes")
        if not v.entry_time:
            raise BadRequestError("El visitante aún no ha ingresado")
        if v.exit_time:
            raise BadRequestError("El visitante ya registró salida")
        v.exit_time = datetime.utcnow()
        await self._repo.commit()
        await self._repo.refresh(v)
        return self._out(v)

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
        if v.entry_time is None:
            status = 'pre_registered'
        elif v.exit_time is None:
            status = 'active'
        else:
            status = 'exited'

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
            phone=v.phone,
            reason=v.reason,
            expected_date=v.expected_date,
            expected_time=v.expected_time,
            reference_code=v.reference_code,
            entry_time=v.entry_time,
            exit_time=v.exit_time,
            notes=v.notes,
            created_at=v.created_at,
            status=status,
        ).model_dump()
