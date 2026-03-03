"""PQRS models (Peticiones, Quejas, Reclamos, Sugerencias)."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import TimestampCreatedMixin, TimestampMixin
from app.models._tenant import TenantModel

if TYPE_CHECKING:
    from app.models.catalog import PqrStatus, PqrType, Priority
    from app.models.core import Property, User


class Pqr(TenantModel, TimestampMixin, Base):
    __tablename__ = "pqrs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="SET NULL"),
    )
    reported_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"),
    )
    pqr_type_id: Mapped[int] = mapped_column(ForeignKey("pqr_types.id"), nullable=False)
    priority_id: Mapped[int] = mapped_column(ForeignKey("priorities.id"), nullable=False)
    pqr_status_id: Mapped[int] = mapped_column(ForeignKey("pqr_statuses.id"), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    resolved_at: Mapped[Optional[datetime]] = mapped_column()

    pqr_type: Mapped["PqrType"] = relationship(lazy="joined")
    priority: Mapped["Priority"] = relationship(lazy="joined")
    pqr_status: Mapped["PqrStatus"] = relationship(lazy="joined")
    reporter: Mapped["User"] = relationship(foreign_keys=[reported_by], lazy="joined")
    assignee: Mapped[Optional["User"]] = relationship(foreign_keys=[assigned_to], lazy="selectin")
    property: Mapped[Optional["Property"]] = relationship(lazy="selectin")
    comments: Mapped[list["PqrComment"]] = relationship(back_populates="pqr", lazy="selectin")


class PqrComment(TimestampCreatedMixin, Base):
    __tablename__ = "pqr_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pqr_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pqrs.id", ondelete="CASCADE"), nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    comment: Mapped[str] = mapped_column(Text, nullable=False)

    pqr: Mapped["Pqr"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship(lazy="joined")
