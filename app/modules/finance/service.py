"""Finance service."""

from __future__ import annotations

from uuid import UUID

from app.core.enums import PaymentStatusEnum
from app.core.exceptions import BadRequestError, InternalError, NotFoundError
from app.models.finance import Invoice, Payment
from app.modules.finance.repository import FinanceRepository
from app.schemas.finance import (
    ChargeTypeOut,
    InvoiceCreate,
    InvoiceOut,
    PaymentCreate,
    PaymentOut,
)


class FinanceService:
    def __init__(self, repo: FinanceRepository) -> None:
        self._repo = repo

    # ── Charge Types ──────────────────────────────────────────────────────

    async def list_charge_types(self, cid: UUID):
        items = await self._repo.list_charge_types(cid)
        result = []
        for ct in items:
            out = ChargeTypeOut.model_validate(ct).model_dump()
            out["charge_category_name"] = ct.charge_category.name if ct.charge_category else None
            result.append(out)
        return result

    async def create_charge_type(self, body, cid: UUID):
        ct = await self._repo.create_charge_type(cid, body.model_dump())
        out = ChargeTypeOut.model_validate(ct).model_dump()
        out["charge_category_name"] = ct.charge_category.name if ct.charge_category else None
        return out

    # ── Invoices ──────────────────────────────────────────────────────────

    async def list_invoices(self, cid, property_id, payment_status_code, billing_period, offset, limit):
        invoices = await self._repo.list_invoices(
            cid,
            property_id=property_id,
            payment_status_code=payment_status_code,
            billing_period=billing_period,
            offset=offset,
            limit=limit,
        )
        return [self._invoice_out(inv) for inv in invoices]

    async def get_invoice(self, invoice_id: UUID, cid: UUID):
        inv = await self._repo.get_invoice(invoice_id, cid)
        if not inv:
            raise NotFoundError("Factura no encontrada")
        return self._invoice_out(inv)

    async def create_invoice(self, body: InvoiceCreate, cid: UUID):
        prop = await self._repo.get_property(body.property_id, cid)
        if not prop:
            raise NotFoundError("Propiedad no encontrada")

        pending = await self._repo.get_payment_status_by_code("pendiente")
        if not pending:
            raise InternalError("Estado 'pendiente' no configurado")

        inv = Invoice(
            condominium_id=cid,
            property_id=body.property_id,
            charge_type_id=body.charge_type_id,
            payment_status_id=pending.id,
            description=body.description,
            amount=body.amount,
            balance=body.amount,
            due_date=body.due_date,
            billing_period=body.billing_period,
        )
        inv = await self._repo.create_invoice(inv)
        return self._invoice_out(inv)

    # ── Payments ──────────────────────────────────────────────────────────

    async def list_payments(self, invoice_id: UUID, cid: UUID):
        inv = await self._repo.get_invoice(invoice_id, cid)
        if not inv:
            raise NotFoundError("Factura no encontrada")
        payments = await self._repo.list_payments(invoice_id)
        return [self._payment_out(p) for p in payments]

    async def register_payment(self, body: PaymentCreate, cid: UUID, user_id: UUID):
        inv = await self._repo.get_invoice(body.invoice_id, cid)
        if not inv:
            raise NotFoundError("Factura no encontrada")
        if body.amount_paid > float(inv.balance):
            raise BadRequestError(f"Monto excede el saldo pendiente (${inv.balance:,.2f})")

        payment = Payment(
            invoice_id=body.invoice_id,
            amount_paid=body.amount_paid,
            payment_method_id=body.payment_method_id,
            reference=body.reference,
            notes=body.notes,
            received_by=user_id,
        )
        payment = await self._repo.create_payment(payment)
        return self._payment_out(payment)

    # ── Balance ───────────────────────────────────────────────────────────

    async def get_property_balance(self, property_id: UUID, cid: UUID):
        prop = await self._repo.get_property(property_id, cid)
        if not prop:
            raise NotFoundError("Propiedad no encontrada")

        invoices = await self._repo.get_property_invoices(property_id)
        total_charged = sum(float(i.amount) for i in invoices)
        total_balance = sum(float(i.balance) for i in invoices)

        return {
            "property_id": str(property_id),
            "property_number": prop.number,
            "block": prop.block,
            "total_charged": total_charged,
            "total_paid": total_charged - total_balance,
            "total_pending": total_balance,
            "invoice_count": len(invoices),
        }

    async def mark_overdue(self):
        await self._repo.mark_overdue()

    # ── Mappers ───────────────────────────────────────────────────────────

    @staticmethod
    def _invoice_out(inv: Invoice) -> dict:
        return InvoiceOut(
            id=inv.id,
            condominium_id=inv.condominium_id,
            property_id=inv.property_id,
            property_number=inv.property.number if inv.property else None,
            property_block=inv.property.block if inv.property else None,
            charge_type_id=inv.charge_type_id,
            charge_type_name=inv.charge_type.name if inv.charge_type else None,
            payment_status_id=inv.payment_status_id,
            payment_status_name=inv.payment_status.name if inv.payment_status else None,
            description=inv.description,
            amount=float(inv.amount),
            balance=float(inv.balance),
            due_date=inv.due_date,
            billing_period=inv.billing_period,
            paid_at=inv.paid_at,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
        ).model_dump()

    @staticmethod
    def _payment_out(p: Payment) -> dict:
        return PaymentOut(
            id=p.id,
            invoice_id=p.invoice_id,
            amount_paid=float(p.amount_paid),
            payment_method_id=p.payment_method_id,
            payment_method_name=p.payment_method.name if p.payment_method else None,
            reference=p.reference,
            notes=p.notes,
            received_by=p.received_by,
            payment_date=p.payment_date,
            created_at=p.created_at,
        ).model_dump()
