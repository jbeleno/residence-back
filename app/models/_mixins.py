"""Shared SQLAlchemy column mixins."""

from __future__ import annotations

from typing import Optional
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampCreatedMixin:
    __abstract__ = True
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(),
    )


class TimestampMixin(TimestampCreatedMixin):
    __abstract__ = True
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now(),
    )


class SoftDeleteMixin(TimestampMixin):
    __abstract__ = True
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        default=None, nullable=True,
    )
