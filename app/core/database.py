"""Async SQLAlchemy 2.0 engine, session factory, and declarative base."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def _ensure_async_url(url: str) -> str:
    """Convert a sync PostgreSQL URL to an asyncpg one if needed."""
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    # asyncpg uses 'ssl' param instead of libpq's 'sslmode'
    url = url.replace("sslmode=require", "ssl=require")
    url = url.replace("channel_binding=require", "")
    # clean up trailing ? or & artifacts
    url = url.rstrip("&").rstrip("?")
    return url


engine = create_async_engine(
    _ensure_async_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
