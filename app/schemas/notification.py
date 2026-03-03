"""Notification schemas."""

from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    user_id: UUID
    notification_type_id: int
    title: str
    body: str
    reference_type: str | None = None
    reference_id: UUID | None = None


class NotificationMarkRead(BaseModel):
    notification_ids: list[UUID]


class NotificationOut(BaseModel):
    id: UUID
    condominium_id: UUID
    user_id: UUID
    notification_type_id: int
    title: str
    body: str
    reference_type: str | None = None
    reference_id: UUID | None = None
    is_read: bool = False
    read_at: datetime | None = None
    is_push_sent: bool = False
    push_sent_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
