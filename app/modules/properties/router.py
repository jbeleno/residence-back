"""Property router."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    get_current_condominium_id,
    get_current_role,
    require_admin,
    require_authenticated,
    require_super_admin,
)
from app.core.responses import success
from app.modules.properties.repository import PropertyRepository
from app.modules.properties.service import PropertyService
from app.schemas.property import (
    PropertyCreate,
    PropertyUpdate,
    UserPropertyCreate,
    UserPropertyTransfer,
    UserPropertyUpdate,
)

router = APIRouter(prefix="/properties", tags=["Propiedades"])


def _service(db: AsyncSession = Depends(get_db)) -> PropertyService:
    return PropertyService(PropertyRepository(db))


@router.get("/", dependencies=[Depends(require_authenticated)])
async def list_properties(
    cid: UUID = Depends(get_current_condominium_id),
    is_short_rent: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    svc: PropertyService = Depends(_service),
):
    items = await svc.list_properties(cid, is_short_rent, skip, limit)
    return success(items)


@router.get("/{property_id}", dependencies=[Depends(require_authenticated)])
async def get_property(
    property_id: UUID,
    cid: UUID = Depends(get_current_condominium_id),
    svc: PropertyService = Depends(_service),
):
    return success(await svc.get_property(property_id, cid))


@router.post("/", dependencies=[Depends(require_admin)], status_code=201)
async def create_property(
    body: PropertyCreate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: PropertyService = Depends(_service),
):
    return success(await svc.create_property(body, cid))


@router.patch("/{property_id}", dependencies=[Depends(require_admin)])
async def update_property(
    property_id: UUID,
    body: PropertyUpdate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: PropertyService = Depends(_service),
):
    return success(await svc.update_property(property_id, body, cid))


@router.post("/{property_id}/restore", dependencies=[Depends(require_super_admin)])
async def restore_property(
    property_id: UUID,
    svc: PropertyService = Depends(_service),
):
    """Restaurar una propiedad soft-deleted (solo super_admin)."""
    return success(await svc.restore_property(property_id))


# ── Residents ────────────────────────────────────────────────────────────


@router.get("/{property_id}/residents", dependencies=[Depends(require_authenticated)])
async def list_property_residents(
    property_id: UUID,
    cid: UUID = Depends(get_current_condominium_id),
    active_only: bool = True,
    svc: PropertyService = Depends(_service),
):
    items = await svc.list_residents(property_id, cid, active_only)
    return success(items)


@router.post("/residents", dependencies=[Depends(require_admin)], status_code=201)
async def assign_resident(
    body: UserPropertyCreate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: PropertyService = Depends(_service),
):
    return success(await svc.assign_resident(body, cid))


@router.patch("/residents/{assignment_id}", dependencies=[Depends(require_admin)])
async def update_resident_assignment(
    assignment_id: int,
    body: UserPropertyUpdate,
    svc: PropertyService = Depends(_service),
):
    return success(await svc.update_assignment(assignment_id, body))


@router.post("/residents/{assignment_id}/transfer", dependencies=[Depends(require_admin)])
async def transfer_resident(
    assignment_id: int,
    body: UserPropertyTransfer,
    cid: UUID = Depends(get_current_condominium_id),
    role: str = Depends(get_current_role),
    svc: PropertyService = Depends(_service),
):
    """Transfer a resident to another property.

    - Same condominium: admin or super_admin
    - Different condominium: super_admin only
    """
    return success(await svc.transfer_resident(assignment_id, body, cid, role))
