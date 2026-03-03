"""Property service."""

from __future__ import annotations

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.properties.repository import PropertyRepository
from app.schemas.property import (
    PropertyCreate,
    PropertyOut,
    PropertyUpdate,
    UserPropertyCreate,
    UserPropertyOut,
    UserPropertyUpdate,
)


class PropertyService:
    def __init__(self, repo: PropertyRepository) -> None:
        self._repo = repo

    # ── Properties ────────────────────────────────────────────────────────

    async def list_properties(self, cid: UUID, is_short_rent, offset, limit):
        props = await self._repo.list_by_condo(cid, is_short_rent=is_short_rent, offset=offset, limit=limit)
        return [self._prop_out(p) for p in props]

    async def get_property(self, property_id: UUID, cid: UUID):
        p = await self._repo.get_by_id(property_id, cid)
        if not p:
            raise NotFoundError("Propiedad no encontrada")
        return self._prop_out(p)

    async def create_property(self, body: PropertyCreate, cid: UUID):
        p = await self._repo.create(cid, body.model_dump())
        return self._prop_out(p)

    async def update_property(self, property_id: UUID, body: PropertyUpdate, cid: UUID):
        p = await self._repo.get_by_id(property_id, cid)
        if not p:
            raise NotFoundError("Propiedad no encontrada")
        p = await self._repo.update(p, body.model_dump(exclude_unset=True))
        return self._prop_out(p)

    # ── Residents ─────────────────────────────────────────────────────────

    async def list_residents(self, property_id: UUID, cid: UUID, active_only: bool):
        p = await self._repo.get_by_id(property_id, cid)
        if not p:
            raise NotFoundError("Propiedad no encontrada")
        ups = await self._repo.list_residents(property_id, active_only=active_only)
        return [self._up_out(up) for up in ups]

    async def assign_resident(self, body: UserPropertyCreate, cid: UUID):
        p = await self._repo.get_by_id(body.property_id, cid)
        if not p:
            raise NotFoundError("Propiedad no encontrada en este condominio")
        up = await self._repo.create_assignment(body.model_dump())
        return self._up_out(up)

    async def update_assignment(self, aid: int, body: UserPropertyUpdate):
        up = await self._repo.get_assignment_by_id(aid)
        if not up:
            raise NotFoundError("Asignación no encontrada")
        up = await self._repo.update_assignment(up, body.model_dump(exclude_unset=True))
        return self._up_out(up)

    # ── Mappers ───────────────────────────────────────────────────────────

    @staticmethod
    def _prop_out(p) -> dict:
        out = PropertyOut.model_validate(p).model_dump()
        out["property_type_name"] = p.property_type.name if p.property_type else None
        return out

    @staticmethod
    def _up_out(up) -> dict:
        out = UserPropertyOut.model_validate(up).model_dump()
        out["relation_type_name"] = up.relation_type.name if up.relation_type else None
        out["user_full_name"] = up.user.full_name if up.user else None
        return out
