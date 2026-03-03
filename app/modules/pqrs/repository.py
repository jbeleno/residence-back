"""PQR repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import PqrStatus
from app.models.pqr import Pqr, PqrComment


class PqrRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_pqrs(
        self,
        cid: UUID,
        *,
        status_id: int | None = None,
        type_id: int | None = None,
        property_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Pqr]:
        stmt = (
            select(Pqr)
            .options(
                selectinload(Pqr.reporter),
                selectinload(Pqr.assignee),
                selectinload(Pqr.pqr_type),
                selectinload(Pqr.priority),
                selectinload(Pqr.pqr_status),
            )
            .where(Pqr.condominium_id == cid)
        )
        if status_id:
            stmt = stmt.where(Pqr.pqr_status_id == status_id)
        if type_id:
            stmt = stmt.where(Pqr.pqr_type_id == type_id)
        if property_id:
            stmt = stmt.where(Pqr.property_id == property_id)
        stmt = stmt.order_by(Pqr.created_at.desc()).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, pqr_id: UUID, cid: UUID) -> Pqr | None:
        result = await self._db.execute(
            select(Pqr)
            .options(
                selectinload(Pqr.reporter),
                selectinload(Pqr.assignee),
                selectinload(Pqr.pqr_type),
                selectinload(Pqr.priority),
                selectinload(Pqr.pqr_status),
            )
            .where(Pqr.id == pqr_id, Pqr.condominium_id == cid)
        )
        return result.scalars().first()

    async def get_status_by_code(self, code: str) -> PqrStatus | None:
        result = await self._db.execute(
            select(PqrStatus).where(PqrStatus.code == code)
        )
        return result.scalars().first()

    async def create(self, pqr: Pqr) -> Pqr:
        self._db.add(pqr)
        await self._db.commit()
        await self._db.refresh(pqr)
        return pqr

    async def commit(self) -> None:
        await self._db.commit()

    async def refresh(self, obj) -> None:
        await self._db.refresh(obj)

    # ── Comments ──────────────────────────────────────────────────────────

    async def list_comments(self, pqr_id: UUID) -> list[PqrComment]:
        result = await self._db.execute(
            select(PqrComment)
            .options(selectinload(PqrComment.user))
            .where(PqrComment.pqr_id == pqr_id)
            .order_by(PqrComment.created_at)
        )
        return list(result.scalars().all())

    async def add_comment(self, comment: PqrComment) -> PqrComment:
        self._db.add(comment)
        await self._db.commit()
        await self._db.refresh(comment)
        return comment
