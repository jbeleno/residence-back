"""Condominium router."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    get_current_condominium_id,
    require_admin,
    require_super_admin,
)
from app.core.responses import success, success_list
from app.modules.condominiums.repository import CondominiumRepository
from app.modules.condominiums.service import CondominiumService
from app.schemas.condominium import CondominiumCreate, CondominiumOut, CondominiumUpdate

router = APIRouter(prefix="/condominiums", tags=["Condominios"])


def _service(db: AsyncSession = Depends(get_db)) -> CondominiumService:
    return CondominiumService(CondominiumRepository(db))


@router.get("/", dependencies=[Depends(require_super_admin)])
async def list_condominiums(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    svc: CondominiumService = Depends(_service),
):
    items, total = await svc.list_condominiums(skip, limit)
    return success_list(
        [CondominiumOut.model_validate(c).model_dump() for c in items],
        total=total,
    )


@router.get("/current", dependencies=[Depends(require_admin)])
async def get_current_condominium(
    cid: UUID = Depends(get_current_condominium_id),
    svc: CondominiumService = Depends(_service),
):
    condo = await svc.get_current(cid)
    return success(CondominiumOut.model_validate(condo).model_dump())


@router.post("/", dependencies=[Depends(require_super_admin)], status_code=201)
async def create_condominium(
    body: CondominiumCreate,
    svc: CondominiumService = Depends(_service),
):
    condo = await svc.create(body)
    return success(CondominiumOut.model_validate(condo).model_dump())


@router.patch("/current", dependencies=[Depends(require_admin)])
async def update_condominium(
    body: CondominiumUpdate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: CondominiumService = Depends(_service),
):
    condo = await svc.update(cid, body)
    return success(CondominiumOut.model_validate(condo).model_dump())


@router.delete("/current", dependencies=[Depends(require_super_admin)])
async def soft_delete_condominium(
    cid: UUID = Depends(get_current_condominium_id),
    svc: CondominiumService = Depends(_service),
):
    await svc.soft_delete(cid)
    return success({"message": "Condominio eliminado"})
