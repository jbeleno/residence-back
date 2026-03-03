"""PQR service."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.core.enums import PqrStatusEnum
from app.core.exceptions import InternalError, NotFoundError
from app.models.pqr import Pqr, PqrComment
from app.modules.pqrs.repository import PqrRepository
from app.schemas.pqr import PqrCommentCreate, PqrCommentOut, PqrCreate, PqrOut, PqrUpdate


class PqrService:
    def __init__(self, repo: PqrRepository) -> None:
        self._repo = repo

    async def list_pqrs(self, cid, status_id, type_id, property_id, offset, limit):
        items = await self._repo.list_pqrs(
            cid, status_id=status_id, type_id=type_id, property_id=property_id, offset=offset, limit=limit,
        )
        return [self._pqr_out(p) for p in items]

    async def get_pqr(self, pqr_id: UUID, cid: UUID):
        pqr = await self._repo.get_by_id(pqr_id, cid)
        if not pqr:
            raise NotFoundError("PQRS no encontrada")
        return self._pqr_out(pqr)

    async def create_pqr(self, body: PqrCreate, cid: UUID, user_id: UUID):
        open_status = await self._repo.get_status_by_code("abierto")
        if not open_status:
            raise InternalError("Estado 'abierto' no configurado")

        pqr = Pqr(
            condominium_id=cid,
            reported_by=user_id,
            pqr_status_id=open_status.id,
            **body.model_dump(),
        )
        pqr = await self._repo.create(pqr)
        return self._pqr_out(pqr)

    async def update_pqr(self, pqr_id: UUID, body: PqrUpdate, cid: UUID):
        pqr = await self._repo.get_by_id(pqr_id, cid)
        if not pqr:
            raise NotFoundError("PQRS no encontrada")

        data = body.model_dump(exclude_unset=True)

        if "pqr_status_id" in data:
            resolved = await self._repo.get_status_by_code("resuelto")
            if resolved and data["pqr_status_id"] == resolved.id:
                pqr.resolved_at = datetime.utcnow()

        for k, v in data.items():
            setattr(pqr, k, v)
        await self._repo.commit()
        await self._repo.refresh(pqr)
        return self._pqr_out(pqr)

    # ── Comments ──────────────────────────────────────────────────────────

    async def list_comments(self, pqr_id: UUID, cid: UUID):
        pqr = await self._repo.get_by_id(pqr_id, cid)
        if not pqr:
            raise NotFoundError("PQRS no encontrada")
        comments = await self._repo.list_comments(pqr_id)
        return [self._comment_out(c) for c in comments]

    async def add_comment(self, pqr_id: UUID, body: PqrCommentCreate, cid: UUID, user_id: UUID):
        pqr = await self._repo.get_by_id(pqr_id, cid)
        if not pqr:
            raise NotFoundError("PQRS no encontrada")
        comment = PqrComment(pqr_id=pqr_id, user_id=user_id, comment=body.comment)
        comment = await self._repo.add_comment(comment)
        return self._comment_out(comment)

    # ── Mappers ───────────────────────────────────────────────────────────

    @staticmethod
    def _pqr_out(p: Pqr) -> dict:
        return PqrOut(
            id=p.id,
            condominium_id=p.condominium_id,
            property_id=p.property_id,
            reported_by=p.reported_by,
            reporter_name=p.reporter.full_name if p.reporter else None,
            assigned_to=p.assigned_to,
            assignee_name=p.assignee.full_name if p.assignee else None,
            pqr_type_id=p.pqr_type_id,
            pqr_type_name=p.pqr_type.name if p.pqr_type else None,
            priority_id=p.priority_id,
            priority_name=p.priority.name if p.priority else None,
            pqr_status_id=p.pqr_status_id,
            pqr_status_name=p.pqr_status.name if p.pqr_status else None,
            subject=p.subject,
            description=p.description,
            resolution=p.resolution,
            resolved_at=p.resolved_at,
            created_at=p.created_at,
            updated_at=p.updated_at,
        ).model_dump()

    @staticmethod
    def _comment_out(c: PqrComment) -> dict:
        return PqrCommentOut(
            id=c.id,
            pqr_id=c.pqr_id,
            user_id=c.user_id,
            user_name=c.user.full_name if c.user else None,
            comment=c.comment,
            created_at=c.created_at,
        ).model_dump()
