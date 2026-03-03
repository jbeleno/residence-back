"""Pet router."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_condominium_id, require_admin, require_authenticated
from app.core.responses import success
from app.modules.pets.repository import PetRepository
from app.modules.pets.service import PetService
from app.schemas.pet import PetCreate, PetUpdate

router = APIRouter(prefix="/pets", tags=["Mascotas"])


def _service(db: AsyncSession = Depends(get_db)) -> PetService:
    return PetService(PetRepository(db))


@router.get("/", dependencies=[Depends(require_authenticated)])
async def list_pets(
    cid: UUID = Depends(get_current_condominium_id),
    property_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    svc: PetService = Depends(_service),
):
    return success(await svc.list_pets(cid, property_id, skip, limit))


@router.get("/{pet_id}", dependencies=[Depends(require_authenticated)])
async def get_pet(
    pet_id: int,
    cid: UUID = Depends(get_current_condominium_id),
    svc: PetService = Depends(_service),
):
    return success(await svc.get_pet(pet_id, cid))


@router.post("/", dependencies=[Depends(require_authenticated)], status_code=201)
async def create_pet(
    body: PetCreate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: PetService = Depends(_service),
):
    return success(await svc.create_pet(body, cid))


@router.patch("/{pet_id}", dependencies=[Depends(require_authenticated)])
async def update_pet(
    pet_id: int,
    body: PetUpdate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: PetService = Depends(_service),
):
    return success(await svc.update_pet(pet_id, body, cid))
