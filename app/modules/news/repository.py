"""News repository."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.news import NewsBoard


class NewsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_news(
        self,
        cid: UUID,
        *,
        published_only: bool = True,
        offset: int = 0,
        limit: int = 20,
    ) -> list[NewsBoard]:
        stmt = (
            select(NewsBoard)
            .options(selectinload(NewsBoard.author))
            .where(NewsBoard.condominium_id == cid)
        )
        if published_only:
            now = datetime.utcnow()
            stmt = stmt.where(
                NewsBoard.is_published.is_(True),
                (NewsBoard.expires_at.is_(None)) | (NewsBoard.expires_at > now),
            )
        stmt = stmt.order_by(NewsBoard.is_pinned.desc(), NewsBoard.publish_date.desc()).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, news_id: int, cid: UUID) -> NewsBoard | None:
        result = await self._db.execute(
            select(NewsBoard)
            .options(selectinload(NewsBoard.author))
            .where(NewsBoard.id == news_id, NewsBoard.condominium_id == cid)
        )
        return result.scalars().first()

    async def create(self, news: NewsBoard) -> NewsBoard:
        self._db.add(news)
        await self._db.commit()
        await self._db.refresh(news)
        return news

    async def update(self, news: NewsBoard, data: dict) -> NewsBoard:
        for k, v in data.items():
            setattr(news, k, v)
        await self._db.commit()
        await self._db.refresh(news)
        return news

    async def delete(self, news: NewsBoard) -> None:
        await self._db.delete(news)
        await self._db.commit()
