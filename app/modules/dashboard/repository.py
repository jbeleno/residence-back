"""Dashboard repository – aggregated queries for the admin dashboard."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.core import Property, UserProperty
from app.models.finance import Invoice, Payment
from app.models.pqr import Pqr
from app.models.visitor import VisitorLog


class DashboardRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def count_properties(self, cid: UUID) -> int:
        result = await self._db.execute(
            select(func.count(Property.id)).where(
                Property.condominium_id == cid,
                Property.is_active.is_(True),
                Property.deleted_at.is_(None),
            )
        )
        return result.scalar() or 0

    async def count_active_residents(self, cid: UUID) -> int:
        result = await self._db.execute(
            select(func.count(func.distinct(UserProperty.user_id))).where(
                UserProperty.property_id.in_(
                    select(Property.id).where(
                        Property.condominium_id == cid,
                        Property.deleted_at.is_(None),
                    )
                ),
                UserProperty.is_active.is_(True),
            )
        )
        return result.scalar() or 0

    async def pending_payments_total(self, cid: UUID) -> float:
        result = await self._db.execute(
            select(func.coalesce(func.sum(Invoice.balance), 0)).where(
                Invoice.condominium_id == cid,
                Invoice.balance > 0,
            )
        )
        return float(result.scalar() or 0)

    async def count_open_pqrs(self, cid: UUID) -> int:
        result = await self._db.execute(
            select(func.count(Pqr.id)).where(
                Pqr.condominium_id == cid,
                Pqr.resolved_at.is_(None),
            )
        )
        return result.scalar() or 0

    async def active_visitors(self, cid: UUID, limit: int = 10) -> list:
        result = await self._db.execute(
            select(VisitorLog)
            .options(selectinload(VisitorLog.property))
            .where(
                VisitorLog.condominium_id == cid,
                VisitorLog.exit_time.is_(None),
            )
            .order_by(VisitorLog.entry_time.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def monthly_collections(self, cid: UUID, months: int = 6) -> list[dict]:
        """Return last N months of payment totals."""
        result = await self._db.execute(
            select(
                extract("year", Payment.payment_date).label("year"),
                extract("month", Payment.payment_date).label("month"),
                func.sum(Payment.amount_paid).label("total"),
            )
            .join(Invoice, Payment.invoice_id == Invoice.id)
            .where(Invoice.condominium_id == cid)
            .group_by("year", "month")
            .order_by("year", "month")
            .limit(months)
        )
        return [
            {"year": int(r.year), "month": int(r.month), "total": float(r.total)}
            for r in result.all()
        ]
