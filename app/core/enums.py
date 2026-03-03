"""Python Enums that map to database catalog IDs.

These enums are the *single source of truth* for status comparisons in
business logic.  Never use raw strings like ``"pendiente"`` – always
reference, for example, ``BookingStatusEnum.PENDIENTE``.

**Convention**: ``value`` == ``id`` in the corresponding catalog table.
Seed data in ``001_seed_dev.sql`` must keep IDs in sync with these enums.
"""

from __future__ import annotations

from enum import IntEnum


# ── booking_statuses ──────────────────────────────────────────────────────


class BookingStatusEnum(IntEnum):
    PENDIENTE = 1
    APROBADA = 2
    RECHAZADA = 3
    CANCELADA = 4
    FINALIZADA = 5


# ── payment_statuses ─────────────────────────────────────────────────────


class PaymentStatusEnum(IntEnum):
    PENDIENTE = 1
    PAGADO = 2
    PARCIAL = 3
    VENCIDO = 4
    ANULADO = 5


# ── pqr_statuses ─────────────────────────────────────────────────────────


class PqrStatusEnum(IntEnum):
    ABIERTO = 1
    EN_PROCESO = 2
    RESUELTO = 3
    CERRADO = 4


# ── priorities ────────────────────────────────────────────────────────────


class PriorityEnum(IntEnum):
    BAJA = 1
    MEDIA = 2
    ALTA = 3
    URGENTE = 4
