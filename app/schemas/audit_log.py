"""Audit log schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogOut(BaseModel):
    id: int
    user_id: UUID | None = None
    user_email: str | None = None
    user_role: str | None = None
    condominium_id: UUID | None = None
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    changes: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = Field(default=None)
    ip_address: str | None = None
    user_agent: str | None = None
    method: str | None = None
    path: str | None = None
    status_code: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
