"""PQR router."""

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
from app.modules.pqrs.repository import PqrRepository
from app.modules.pqrs.service import PqrService
from app.schemas.pqr import PqrCommentCreate, PqrCreate, PqrUpdate

router = APIRouter(prefix="/pqrs", tags=["PQRS"])


def _service(db: AsyncSession = Depends(get_db)) -> PqrService:
    return PqrService(PqrRepository(db))


@router.get("/", dependencies=[Depends(require_authenticated)])
async def list_pqrs(
    cid: UUID = Depends(get_current_condominium_id),
    status_id: int | None = None,
    type_id: int | None = None,
    property_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    svc: PqrService = Depends(_service),
):
    return success(await svc.list_pqrs(cid, status_id, type_id, property_id, skip, limit))


@router.get("/{pqr_id}", dependencies=[Depends(require_authenticated)])
async def get_pqr(
    pqr_id: UUID,
    cid: UUID = Depends(get_current_condominium_id),
    svc: PqrService = Depends(_service),
):
    return success(await svc.get_pqr(pqr_id, cid))


@router.post("/", dependencies=[Depends(require_authenticated)], status_code=201)
async def create_pqr(
    body: PqrCreate,
    cid: UUID = Depends(get_current_condominium_id),
    current_user=Depends(get_current_user),
    svc: PqrService = Depends(_service),
):
    return success(await svc.create_pqr(body, cid, current_user.id))


@router.patch("/{pqr_id}", dependencies=[Depends(require_admin)])
async def update_pqr(
    pqr_id: UUID,
    body: PqrUpdate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: PqrService = Depends(_service),
):
    return success(await svc.update_pqr(pqr_id, body, cid))


# ── Comments ──────────────────────────────────────────────────────────────


@router.get("/{pqr_id}/comments", dependencies=[Depends(require_authenticated)])
async def list_pqr_comments(
    pqr_id: UUID,
    cid: UUID = Depends(get_current_condominium_id),
    svc: PqrService = Depends(_service),
):
    return success(await svc.list_comments(pqr_id, cid))


@router.post("/{pqr_id}/comments", dependencies=[Depends(require_authenticated)], status_code=201)
async def add_pqr_comment(
    pqr_id: UUID,
    body: PqrCommentCreate,
    cid: UUID = Depends(get_current_condominium_id),
    current_user=Depends(get_current_user),
    svc: PqrService = Depends(_service),
):
    return success(await svc.add_comment(pqr_id, body, cid, current_user.id))
