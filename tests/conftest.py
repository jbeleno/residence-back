"""Shared test fixtures: async DB engine, session, app client, auth helpers."""

from __future__ import annotations

import asyncio
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password

# Ensure all models are registered with Base.metadata before create_all
import app.models  # noqa: F401

# ── SQLite UUID adapter ───────────────────────────────────────────────────
# PostgreSQL models use dialects.postgresql.UUID; SQLite doesn't know how to
# bind Python uuid.UUID objects.  Register a global adapter so that aiosqlite
# transparently converts them to their string representation.
sqlite3.register_adapter(uuid.UUID, lambda u: str(u))

# ── In-memory SQLite async engine ─────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
test_session_factory = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False,
)


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh async session for each test."""
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx AsyncClient bound to the test app with overridden DB."""
    from app.main import create_app

    app = create_app()

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Auth helpers ──────────────────────────────────────────────────────────


def make_user_id() -> uuid.UUID:
    return uuid.uuid4()


def make_condo_id() -> uuid.UUID:
    return uuid.uuid4()


def make_token(
    user_id: Optional[uuid.UUID] = None,
    cid: Optional[uuid.UUID] = None,
    role: str = "admin",
) -> str:
    """Create a valid JWT for testing."""
    data = {"sub": str(user_id or make_user_id())}
    if cid:
        data["cid"] = str(cid)
    if role:
        data["role"] = role
    return create_access_token(data)


def auth_headers(
    user_id: Optional[uuid.UUID] = None,
    cid: Optional[uuid.UUID] = None,
    role: str = "admin",
) -> dict:
    """Return Authorization header dict for testing endpoints."""
    token = make_token(user_id, cid, role)
    return {"Authorization": f"Bearer {token}"}


# ── Seed helpers ──────────────────────────────────────────────────────────


async def seed_user(
    db: AsyncSession,
    *,
    email: str = "test@example.com",
    password: str = "password123",
    full_name: str = "Test User",
    is_active: bool = True,
) -> MagicMock:
    """Insert a user row into the test DB and return it."""
    from app.models.core import User

    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        is_active=is_active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def seed_condominium(
    db: AsyncSession,
    *,
    name: str = "Condo Test",
    address: str = "Calle 1",
    city: str = "Bogotá",
) -> MagicMock:
    """Insert a condominium row."""
    from app.models.core import Condominium

    condo = Condominium(
        id=uuid.uuid4(),
        name=name,
        address=address,
        city=city,
        country="Colombia",
        timezone="America/Bogota",
        currency="COP",
        visitor_parking_hourly_rate=5000,
    )
    db.add(condo)
    await db.commit()
    await db.refresh(condo)
    return condo


async def seed_role(
    db: AsyncSession,
    *,
    role_name: str = "admin",
) -> MagicMock:
    """Insert a role row."""
    from app.models.core import Role

    role = Role(id=uuid.uuid4(), role_name=role_name)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def seed_user_condo_role(
    db: AsyncSession,
    user_id: uuid.UUID,
    condo_id: uuid.UUID,
    role_id: uuid.UUID,
):
    """Link a user to a condominium with a role."""
    from app.models.core import UserCondominiumRole

    ucr = UserCondominiumRole(
        id=uuid.uuid4(),
        user_id=user_id,
        condominium_id=condo_id,
        role_id=role_id,
        is_active=True,
    )
    db.add(ucr)
    await db.commit()
    return ucr
