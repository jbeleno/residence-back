"""Visitor router."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    get_current_condominium_id,
    get_current_user,
    require_admin_or_guard,
    require_authenticated,
)
from app.core.responses import success
from app.modules.visitors.repository import VisitorRepository
from app.modules.visitors.service import VisitorService
from app.schemas.visitor import VisitorLogCreate

router = APIRouter(prefix="/visitors", tags=["Portería / Visitantes"])


def _service(db: AsyncSession = Depends(get_db)) -> VisitorService:
    return VisitorService(VisitorRepository(db))


@router.get("/", dependencies=[Depends(require_authenticated)])
async def list_visitors(
    cid: UUID = Depends(get_current_condominium_id),
    active_only: bool = False,
    property_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    svc: VisitorService = Depends(_service),
):
    return success(await svc.list_visitors(cid, active_only, property_id, skip, limit))


@router.get("/active", dependencies=[Depends(require_authenticated)])
async def list_active_visitors(
    cid: UUID = Depends(get_current_condominium_id),
    svc: VisitorService = Depends(_service),
):
    return success(await svc.list_active(cid))


@router.get("/{visitor_id}", dependencies=[Depends(require_authenticated)])
async def get_visitor(
    visitor_id: UUID,
    cid: UUID = Depends(get_current_condominium_id),
    svc: VisitorService = Depends(_service),
):
    return success(await svc.get_visitor(visitor_id, cid))


@router.post("/", dependencies=[Depends(require_admin_or_guard)], status_code=201)
async def register_visitor_entry(
    body: VisitorLogCreate,
    cid: UUID = Depends(get_current_condominium_id),
    current_user=Depends(get_current_user),
    svc: VisitorService = Depends(_service),
):
    return success(await svc.register_entry(body, cid, current_user.id))


@router.post("/{visitor_id}/exit", dependencies=[Depends(require_admin_or_guard)])
async def register_visitor_exit(
    visitor_id: UUID,
    cid: UUID = Depends(get_current_condominium_id),
    svc: VisitorService = Depends(_service),
):
    return success(await svc.register_exit(visitor_id, cid))
