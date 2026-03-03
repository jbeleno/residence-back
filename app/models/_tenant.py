"""TenantModel: base mixin that enforces ``condominium_id`` on every
tenant-scoped table.  Models that are NOT tenant-scoped (catalogs, super-admin
tables) do NOT inherit from this mixin.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class TenantModel:
    """Mixin – adds ``condominium_id`` FK with cascade delete."""

    __abstract__ = True

    condominium_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("condominiums.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
