"""News service."""

from __future__ import annotations

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.news import NewsBoard
from app.modules.news.repository import NewsRepository
from app.schemas.news import NewsCreate, NewsOut, NewsUpdate


class NewsService:
    def __init__(self, repo: NewsRepository) -> None:
        self._repo = repo

    async def list_news(self, cid: UUID, published_only: bool, offset: int, limit: int):
        items = await self._repo.list_news(cid, published_only=published_only, offset=offset, limit=limit)
        return [self._out(n) for n in items]

    async def get_news(self, news_id: int, cid: UUID):
        n = await self._repo.get_by_id(news_id, cid)
        if not n:
            raise NotFoundError("Noticia no encontrada")
        return self._out(n)

    async def create_news(self, body: NewsCreate, cid: UUID, author_id: UUID):
        news = NewsBoard(condominium_id=cid, author_id=author_id, **body.model_dump())
        news = await self._repo.create(news)
        return self._out(news)

    async def update_news(self, news_id: int, body: NewsUpdate, cid: UUID):
        n = await self._repo.get_by_id(news_id, cid)
        if not n:
            raise NotFoundError("Noticia no encontrada")
        n = await self._repo.update(n, body.model_dump(exclude_unset=True))
        return self._out(n)

    async def delete_news(self, news_id: int, cid: UUID):
        n = await self._repo.get_by_id(news_id, cid)
        if not n:
            raise NotFoundError("Noticia no encontrada")
        await self._repo.delete(n)

    @staticmethod
    def _out(n: NewsBoard) -> dict:
        return NewsOut(
            id=n.id,
            condominium_id=n.condominium_id,
            author_id=n.author_id,
            author_name=n.author.full_name if n.author else None,
            title=n.title,
            content=n.content,
            is_pinned=n.is_pinned,
            is_published=n.is_published,
            publish_date=n.publish_date,
            expires_at=n.expires_at,
            cover_url=n.cover_url,
            created_at=n.created_at,
            updated_at=n.updated_at,
        ).model_dump()
