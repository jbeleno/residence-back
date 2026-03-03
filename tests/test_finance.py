"""Tests for finance module – service-level with mocked repository."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import BadRequestError, InternalError, NotFoundError
from app.modules.finance.service import FinanceService


# ── Helpers ───────────────────────────────────────────────────────────────


def _uid() -> uuid.UUID:
    return uuid.uuid4()


def _mock_charge_type(ct_id=1, ct_name="Administración"):
    ct = MagicMock()
    ct.id = ct_id
    ct.condominium_id = _uid()
    ct.name = ct_name
    ct.charge_category_id = 1
    cc_mock = MagicMock()
    cc_mock.name = "Cuota"
    ct.charge_category = cc_mock
    ct.default_amount = 100.0
    ct.is_recurring = True
    ct.is_active = True
    return ct


def _mock_invoice(inv_id=None, amount=100, balance=50):
    inv = MagicMock()
    inv.id = inv_id or _uid()
    inv.condominium_id = _uid()
    inv.property_id = _uid()
    inv.charge_type_id = 1
    inv.payment_status_id = 1
    inv.description = "Cuota mensual"
    inv.amount = Decimal(str(amount))
    inv.balance = Decimal(str(balance))
    inv.due_date = date(2025, 3, 1)
    inv.billing_period = "2025-03"
    inv.paid_at = None
    inv.created_at = datetime(2025, 1, 1)
    inv.updated_at = datetime(2025, 1, 1)
    # Related objects — use configure_mock for .name since MagicMock(name=...) sets internal id
    prop_mock = MagicMock()
    prop_mock.number = "101"
    prop_mock.block = "A"
    inv.property = prop_mock
    ct_mock = MagicMock()
    ct_mock.name = "Administración"
    inv.charge_type = ct_mock
    ps_mock = MagicMock()
    ps_mock.name = "Pendiente"
    inv.payment_status = ps_mock
    return inv


def _mock_payment(pay_id=None, amount_paid=50):
    p = MagicMock()
    p.id = pay_id or _uid()
    p.invoice_id = _uid()
    p.amount_paid = Decimal(str(amount_paid))
    p.payment_method_id = 1
    pm_mock = MagicMock()
    pm_mock.name = "Transferencia"
    p.payment_method = pm_mock
    p.reference = "REF001"
    p.notes = None
    p.received_by = _uid()
    p.payment_date = datetime(2025, 2, 15)
    p.created_at = datetime(2025, 2, 15)
    return p


def _mock_property(pid=None, number="101"):
    p = MagicMock()
    p.id = pid or _uid()
    p.number = number
    p.block = "A"
    return p


def _mock_payment_status(ps_id=1, code="pendiente"):
    ps = MagicMock()
    ps.id = ps_id
    ps.code = code
    return ps


def _repo() -> AsyncMock:
    return AsyncMock()


# ══════════════════════════════════════════════════════════════════════════
#  Charge Types
# ══════════════════════════════════════════════════════════════════════════


class TestChargeTypes:
    @pytest.mark.asyncio
    async def test_list_charge_types(self):
        cid = _uid()
        repo = _repo()
        repo.list_charge_types.return_value = [_mock_charge_type(), _mock_charge_type(ct_id=2)]

        svc = FinanceService(repo)
        result = await svc.list_charge_types(cid)
        assert len(result) == 2
        assert all("charge_category_name" in r for r in result)

    @pytest.mark.asyncio
    async def test_create_charge_type(self):
        cid = _uid()
        repo = _repo()
        ct = _mock_charge_type()
        repo.create_charge_type.return_value = ct

        body = MagicMock()
        body.model_dump.return_value = {"name": "Parqueadero", "charge_category_id": 1}

        svc = FinanceService(repo)
        result = await svc.create_charge_type(body, cid)
        assert "charge_category_name" in result


# ══════════════════════════════════════════════════════════════════════════
#  Invoices
# ══════════════════════════════════════════════════════════════════════════


class TestInvoices:
    @pytest.mark.asyncio
    async def test_list_invoices(self):
        cid = _uid()
        repo = _repo()
        repo.list_invoices.return_value = [_mock_invoice(), _mock_invoice()]

        svc = FinanceService(repo)
        result = await svc.list_invoices(cid, None, None, None, 0, 50)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_invoice_found(self):
        inv_id, cid = _uid(), _uid()
        repo = _repo()
        repo.get_invoice.return_value = _mock_invoice(inv_id=inv_id)

        svc = FinanceService(repo)
        result = await svc.get_invoice(inv_id, cid)
        assert result["id"] == inv_id

    @pytest.mark.asyncio
    async def test_get_invoice_not_found(self):
        repo = _repo()
        repo.get_invoice.return_value = None
        svc = FinanceService(repo)
        with pytest.raises(NotFoundError):
            await svc.get_invoice(_uid(), _uid())

    @pytest.mark.asyncio
    async def test_create_invoice_success(self):
        cid = _uid()
        repo = _repo()
        repo.get_property.return_value = _mock_property()
        repo.get_payment_status_by_code.return_value = _mock_payment_status()
        repo.create_invoice.return_value = _mock_invoice()

        from app.schemas.finance import InvoiceCreate
        body = InvoiceCreate(
            property_id=_uid(),
            charge_type_id=1,
            amount=100.0,
            due_date=date(2025, 4, 1),
        )
        svc = FinanceService(repo)
        result = await svc.create_invoice(body, cid)
        assert "amount" in result

    @pytest.mark.asyncio
    async def test_create_invoice_property_not_found(self):
        repo = _repo()
        repo.get_property.return_value = None

        from app.schemas.finance import InvoiceCreate
        body = InvoiceCreate(
            property_id=_uid(), charge_type_id=1, amount=100, due_date=date(2025, 4, 1),
        )
        svc = FinanceService(repo)
        with pytest.raises(NotFoundError):
            await svc.create_invoice(body, _uid())

    @pytest.mark.asyncio
    async def test_create_invoice_no_pending_status(self):
        repo = _repo()
        repo.get_property.return_value = _mock_property()
        repo.get_payment_status_by_code.return_value = None

        from app.schemas.finance import InvoiceCreate
        body = InvoiceCreate(
            property_id=_uid(), charge_type_id=1, amount=100, due_date=date(2025, 4, 1),
        )
        svc = FinanceService(repo)
        with pytest.raises(InternalError):
            await svc.create_invoice(body, _uid())


# ══════════════════════════════════════════════════════════════════════════
#  Payments
# ══════════════════════════════════════════════════════════════════════════


class TestPayments:
    @pytest.mark.asyncio
    async def test_list_payments(self):
        inv_id, cid = _uid(), _uid()
        repo = _repo()
        repo.get_invoice.return_value = _mock_invoice(inv_id=inv_id)
        repo.list_payments.return_value = [_mock_payment()]

        svc = FinanceService(repo)
        result = await svc.list_payments(inv_id, cid)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_payments_invoice_not_found(self):
        repo = _repo()
        repo.get_invoice.return_value = None
        svc = FinanceService(repo)
        with pytest.raises(NotFoundError):
            await svc.list_payments(_uid(), _uid())

    @pytest.mark.asyncio
    async def test_register_payment_success(self):
        cid, uid = _uid(), _uid()
        repo = _repo()
        inv = _mock_invoice(balance=100)
        repo.get_invoice.return_value = inv
        repo.create_payment.return_value = _mock_payment(amount_paid=50)

        from app.schemas.finance import PaymentCreate
        body = PaymentCreate(
            invoice_id=inv.id, amount_paid=50, payment_method_id=1,
        )
        svc = FinanceService(repo)
        result = await svc.register_payment(body, cid, uid)
        assert "amount_paid" in result

    @pytest.mark.asyncio
    async def test_register_payment_exceeds_balance(self):
        repo = _repo()
        inv = _mock_invoice(balance=30)
        repo.get_invoice.return_value = inv

        from app.schemas.finance import PaymentCreate
        body = PaymentCreate(
            invoice_id=inv.id, amount_paid=50, payment_method_id=1,
        )
        svc = FinanceService(repo)
        with pytest.raises(BadRequestError, match="excede"):
            await svc.register_payment(body, _uid(), _uid())


# ══════════════════════════════════════════════════════════════════════════
#  Balance
# ══════════════════════════════════════════════════════════════════════════


class TestBalance:
    @pytest.mark.asyncio
    async def test_get_property_balance(self):
        pid, cid = _uid(), _uid()
        repo = _repo()
        repo.get_property.return_value = _mock_property(pid=pid)
        repo.get_property_invoices.return_value = [
            _mock_invoice(amount=200, balance=100),
            _mock_invoice(amount=100, balance=0),
        ]

        svc = FinanceService(repo)
        result = await svc.get_property_balance(pid, cid)
        assert result["total_charged"] == 300.0
        assert result["total_pending"] == 100.0
        assert result["invoice_count"] == 2

    @pytest.mark.asyncio
    async def test_get_property_balance_not_found(self):
        repo = _repo()
        repo.get_property.return_value = None
        svc = FinanceService(repo)
        with pytest.raises(NotFoundError):
            await svc.get_property_balance(_uid(), _uid())

    @pytest.mark.asyncio
    async def test_mark_overdue(self):
        repo = _repo()
        svc = FinanceService(repo)
        await svc.mark_overdue()
        repo.mark_overdue.assert_awaited_once()
