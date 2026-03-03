"""News router."""

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
from app.modules.news.repository import NewsRepository
from app.modules.news.service import NewsService
from app.schemas.news import NewsCreate, NewsUpdate

router = APIRouter(prefix="/news", tags=["Noticias"])


def _service(db: AsyncSession = Depends(get_db)) -> NewsService:
    return NewsService(NewsRepository(db))


@router.get("/", dependencies=[Depends(require_authenticated)])
async def list_news(
    cid: UUID = Depends(get_current_condominium_id),
    published_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    svc: NewsService = Depends(_service),
):
    return success(await svc.list_news(cid, published_only, skip, limit))


@router.get("/{news_id}", dependencies=[Depends(require_authenticated)])
async def get_news(
    news_id: int,
    cid: UUID = Depends(get_current_condominium_id),
    svc: NewsService = Depends(_service),
):
    return success(await svc.get_news(news_id, cid))


@router.post("/", dependencies=[Depends(require_admin)], status_code=201)
async def create_news(
    body: NewsCreate,
    cid: UUID = Depends(get_current_condominium_id),
    current_user=Depends(get_current_user),
    svc: NewsService = Depends(_service),
):
    return success(await svc.create_news(body, cid, current_user.id))


@router.patch("/{news_id}", dependencies=[Depends(require_admin)])
async def update_news(
    news_id: int,
    body: NewsUpdate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: NewsService = Depends(_service),
):
    return success(await svc.update_news(news_id, body, cid))


@router.delete("/{news_id}", dependencies=[Depends(require_admin)])
async def delete_news(
    news_id: int,
    cid: UUID = Depends(get_current_condominium_id),
    svc: NewsService = Depends(_service),
):
    await svc.delete_news(news_id, cid)
    return success({"message": "Noticia eliminada"})
