"""AuditLog model — immutable trail of every relevant action."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

# Use JSONB on Postgres, plain JSON elsewhere (SQLite for tests).
JSONType = JSONB().with_variant(JSON(), "sqlite")

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Who
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    user_email: Mapped[Optional[str]] = mapped_column(String(150))
    user_role: Mapped[Optional[str]] = mapped_column(String(50))

    # Tenant
    condominium_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("condominiums.id", ondelete="SET NULL"),
        nullable=True,
    )

    # What
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(60))
    entity_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Change diff & extra context
    changes: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONType, nullable=True)
    extra_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSONType, nullable=True,
    )

    # Origin of the request
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    method: Mapped[Optional[str]] = mapped_column(String(10))
    path: Mapped[Optional[str]] = mapped_column(String(500))
    status_code: Mapped[Optional[int]] = mapped_column(Integer)

    # When
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False,
    )
