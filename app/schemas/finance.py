"""Finance schemas."""

from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import date, datetime

from pydantic import BaseModel


class ChargeTypeCreate(BaseModel):
    name: str
    charge_category_id: int
    default_amount: float | None = None
    is_recurring: bool = False


class ChargeTypeOut(BaseModel):
    id: int
    condominium_id: UUID | None = None
    name: str
    charge_category_id: int
    default_amount: float | None = None
    is_recurring: bool = False
    is_active: bool = True

    model_config = {"from_attributes": True}


class InvoiceCreate(BaseModel):
    property_id: UUID
    charge_type_id: int
    description: str | None = None
    amount: float
    due_date: date
    billing_period: str | None = None


class InvoiceOut(BaseModel):
    id: UUID
    condominium_id: UUID
    property_id: UUID
    charge_type_id: int
    charge_type_name: str | None = None
    payment_status_id: int
    payment_status: str | None = None
    description: str | None = None
    amount: float
    balance: float
    due_date: date
    billing_period: str | None = None
    paid_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    invoice_id: UUID
    amount_paid: float
    payment_method_id: int
    reference: str | None = None
    notes: str | None = None


class PaymentOut(BaseModel):
    id: UUID
    invoice_id: UUID
    amount_paid: float
    payment_method_id: int
    reference: str | None = None
    notes: str | None = None
    received_by: UUID | None = None
    payment_date: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class PropertyBalanceOut(BaseModel):
    property_id: UUID
    total_charged: float
    total_paid: float
    balance: float
