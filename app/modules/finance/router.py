"""Finance router."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    get_current_condominium_id,
    get_current_user,
    require_admin,
    require_admin_or_accountant,
    require_authenticated,
)
from app.core.responses import success
from app.modules.finance.repository import FinanceRepository
from app.modules.finance.service import FinanceService
from app.schemas.finance import ChargeTypeCreate, InvoiceCreate, PaymentCreate

router = APIRouter(prefix="/finance", tags=["Finanzas"])


def _service(db: AsyncSession = Depends(get_db)) -> FinanceService:
    return FinanceService(FinanceRepository(db))


# ── Charge Types ──────────────────────────────────────────────────────────


@router.get("/charge-types", dependencies=[Depends(require_authenticated)])
async def list_charge_types(
    cid: UUID = Depends(get_current_condominium_id),
    svc: FinanceService = Depends(_service),
):
    return success(await svc.list_charge_types(cid))


@router.post("/charge-types", dependencies=[Depends(require_admin)], status_code=201)
async def create_charge_type(
    body: ChargeTypeCreate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: FinanceService = Depends(_service),
):
    return success(await svc.create_charge_type(body, cid))


# ── Invoices ──────────────────────────────────────────────────────────────


@router.get("/invoices", dependencies=[Depends(require_authenticated)])
async def list_invoices(
    cid: UUID = Depends(get_current_condominium_id),
    property_id: UUID | None = None,
    payment_status_code: str | None = None,
    billing_period: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    svc: FinanceService = Depends(_service),
):
    return success(await svc.list_invoices(cid, property_id, payment_status_code, billing_period, skip, limit))


@router.get("/invoices/{invoice_id}", dependencies=[Depends(require_authenticated)])
async def get_invoice(
    invoice_id: UUID,
    cid: UUID = Depends(get_current_condominium_id),
    svc: FinanceService = Depends(_service),
):
    return success(await svc.get_invoice(invoice_id, cid))


@router.post("/invoices", dependencies=[Depends(require_admin_or_accountant)], status_code=201)
async def create_invoice(
    body: InvoiceCreate,
    cid: UUID = Depends(get_current_condominium_id),
    svc: FinanceService = Depends(_service),
):
    return success(await svc.create_invoice(body, cid))


# ── Payments ──────────────────────────────────────────────────────────────


@router.get("/invoices/{invoice_id}/payments", dependencies=[Depends(require_authenticated)])
async def list_invoice_payments(
    invoice_id: UUID,
    cid: UUID = Depends(get_current_condominium_id),
    svc: FinanceService = Depends(_service),
):
    return success(await svc.list_payments(invoice_id, cid))


@router.post("/payments", dependencies=[Depends(require_admin_or_accountant)], status_code=201)
async def register_payment(
    body: PaymentCreate,
    cid: UUID = Depends(get_current_condominium_id),
    current_user=Depends(get_current_user),
    svc: FinanceService = Depends(_service),
):
    return success(await svc.register_payment(body, cid, current_user.id))


# ── Balance ───────────────────────────────────────────────────────────────


@router.get("/property-balance/{property_id}", dependencies=[Depends(require_authenticated)])
async def get_property_balance(
    property_id: UUID,
    cid: UUID = Depends(get_current_condominium_id),
    svc: FinanceService = Depends(_service),
):
    return success(await svc.get_property_balance(property_id, cid))


@router.post("/mark-overdue", dependencies=[Depends(require_admin)])
async def mark_overdue_invoices(svc: FinanceService = Depends(_service)):
    await svc.mark_overdue()
    return success({"message": "Facturas vencidas actualizadas"})
