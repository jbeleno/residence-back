"""Finance repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import PaymentStatus
from app.models.core import Property
from app.models.finance import ChargeType, Invoice, Payment


class FinanceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Charge Types ──────────────────────────────────────────────────────

    async def list_charge_types(self, cid: UUID) -> list[ChargeType]:
        stmt = (
            select(ChargeType)
            .options(selectinload(ChargeType.charge_category))
            .where(
                (ChargeType.condominium_id == cid) | (ChargeType.condominium_id.is_(None)),
                ChargeType.is_active.is_(True),
            )
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def create_charge_type(self, cid: UUID, data: dict) -> ChargeType:
        ct = ChargeType(condominium_id=cid, **data)
        self._db.add(ct)
        await self._db.commit()
        await self._db.refresh(ct)
        return ct

    # ── Invoices ──────────────────────────────────────────────────────────

    async def list_invoices(
        self,
        cid: UUID,
        *,
        property_id: UUID | None = None,
        payment_status_code: str | None = None,
        billing_period: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Invoice]:
        stmt = (
            select(Invoice)
            .options(
                selectinload(Invoice.property),
                selectinload(Invoice.charge_type),
                selectinload(Invoice.payment_status),
            )
            .where(Invoice.condominium_id == cid)
        )
        if property_id:
            stmt = stmt.where(Invoice.property_id == property_id)
        if payment_status_code:
            ps = await self.get_payment_status_by_code(payment_status_code)
            if ps:
                stmt = stmt.where(Invoice.payment_status_id == ps.id)
        if billing_period:
            stmt = stmt.where(Invoice.billing_period == billing_period)
        stmt = stmt.order_by(Invoice.due_date.desc()).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_invoice(self, invoice_id: UUID, cid: UUID) -> Invoice | None:
        result = await self._db.execute(
            select(Invoice)
            .options(
                selectinload(Invoice.property),
                selectinload(Invoice.charge_type),
                selectinload(Invoice.payment_status),
            )
            .where(Invoice.id == invoice_id, Invoice.condominium_id == cid)
        )
        return result.scalars().first()

    async def create_invoice(self, inv: Invoice) -> Invoice:
        self._db.add(inv)
        await self._db.commit()
        await self._db.refresh(inv)
        return inv

    # ── Payments ──────────────────────────────────────────────────────────

    async def list_payments(self, invoice_id: UUID) -> list[Payment]:
        result = await self._db.execute(
            select(Payment)
            .options(selectinload(Payment.payment_method))
            .where(Payment.invoice_id == invoice_id)
            .order_by(Payment.payment_date)
        )
        return list(result.scalars().all())

    async def create_payment(self, payment: Payment) -> Payment:
        self._db.add(payment)
        await self._db.commit()
        await self._db.refresh(payment)
        return payment

    # ── Balance ───────────────────────────────────────────────────────────

    async def get_property(self, property_id: UUID, cid: UUID) -> Property | None:
        result = await self._db.execute(
            select(Property).where(Property.id == property_id, Property.condominium_id == cid)
        )
        return result.scalars().first()

    async def get_property_invoices(self, property_id: UUID) -> list[Invoice]:
        result = await self._db.execute(
            select(Invoice).where(Invoice.property_id == property_id)
        )
        return list(result.scalars().all())

    # ── Helpers ───────────────────────────────────────────────────────────

    async def get_payment_status_by_code(self, code: str) -> PaymentStatus | None:
        result = await self._db.execute(
            select(PaymentStatus).where(PaymentStatus.code == code)
        )
        return result.scalars().first()

    async def mark_overdue(self) -> None:
        await self._db.execute(text("SELECT fn_mark_overdue_invoices()"))
        await self._db.commit()
