"""Notification model (push + in-app)."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import TimestampCreatedMixin
from app.models._tenant import TenantModel

if TYPE_CHECKING:
    from app.models.catalog import NotificationType
    from app.models.core import User


class Notification(TenantModel, TimestampCreatedMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    notification_type_id: Mapped[int] = mapped_column(
        ForeignKey("notification_types.id"), nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50))
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column()
    is_push_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    push_sent_at: Mapped[Optional[datetime]] = mapped_column()

    notification_type: Mapped["NotificationType"] = relationship(lazy="joined")
    user: Mapped["User"] = relationship(lazy="selectin")
