"""Catalog router."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin, require_authenticated
from app.core.responses import success
from app.modules.catalogs.repository import CatalogRepository
from app.modules.catalogs.service import CatalogService
from app.schemas.catalog import CatalogCreate, CatalogUpdate

router = APIRouter(prefix="/catalogs", tags=["Catálogos"])


def _service(db: AsyncSession = Depends(get_db)) -> CatalogService:
    return CatalogService(CatalogRepository(db))


@router.get("/{catalog_name}", dependencies=[Depends(require_authenticated)])
async def list_catalog(
    catalog_name: str,
    active_only: bool = True,
    svc: CatalogService = Depends(_service),
):
    items = await svc.list_catalog(catalog_name, active_only)
    return success([dict(row.__dict__) for row in items] if items else [])


@router.get("/{catalog_name}/{item_id}", dependencies=[Depends(require_authenticated)])
async def get_catalog_item(
    catalog_name: str,
    item_id: int,
    svc: CatalogService = Depends(_service),
):
    item = await svc.get_item(catalog_name, item_id)
    return success(dict(item.__dict__))


@router.post("/{catalog_name}", dependencies=[Depends(require_admin)], status_code=201)
async def create_catalog_item(
    catalog_name: str,
    body: CatalogCreate,
    svc: CatalogService = Depends(_service),
):
    item = await svc.create_item(catalog_name, body.model_dump())
    return success(dict(item.__dict__))


@router.patch("/{catalog_name}/{item_id}", dependencies=[Depends(require_admin)])
async def update_catalog_item(
    catalog_name: str,
    item_id: int,
    body: CatalogUpdate,
    svc: CatalogService = Depends(_service),
):
    item = await svc.update_item(catalog_name, item_id, body.model_dump(exclude_unset=True))
    return success(dict(item.__dict__))
