"""Catalog service."""

from __future__ import annotations

from app.core.exceptions import NotFoundError
from app.modules.catalogs.repository import CatalogRepository


class CatalogService:
    def __init__(self, repo: CatalogRepository) -> None:
        self._repo = repo

    def _resolve(self, catalog_name: str):
        model = self._repo.resolve_model(catalog_name)
        if model is None:
            raise NotFoundError(f"Catálogo '{catalog_name}' no encontrado")
        return model

    async def list_catalog(self, catalog_name: str, active_only: bool = True):
        model = self._resolve(catalog_name)
        return await self._repo.list_all(model, active_only=active_only)

    async def get_item(self, catalog_name: str, item_id: int):
        model = self._resolve(catalog_name)
        item = await self._repo.get_by_id(model, item_id)
        if item is None:
            raise NotFoundError("Elemento no encontrado")
        return item

    async def create_item(self, catalog_name: str, data: dict):
        model = self._resolve(catalog_name)
        return await self._repo.create(model, data)

    async def update_item(self, catalog_name: str, item_id: int, data: dict):
        model = self._resolve(catalog_name)
        item = await self._repo.get_by_id(model, item_id)
        if item is None:
            raise NotFoundError("Elemento no encontrado")
        return await self._repo.update(item, data)
