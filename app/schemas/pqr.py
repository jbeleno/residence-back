"""PQRS schemas."""

from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class PqrCreate(BaseModel):
    property_id: UUID | None = None
    pqr_type_id: int
    priority_id: int
    subject: str
    description: str


class PqrUpdate(BaseModel):
    pqr_status_id: int | None = None
    priority_id: int | None = None
    assigned_to: UUID | None = None
    resolution: str | None = None


class PqrOut(BaseModel):
    id: UUID
    condominium_id: UUID
    property_id: UUID | None = None
    reported_by: UUID
    reporter_name: str | None = None
    assigned_to: UUID | None = None
    assignee_name: str | None = None
    pqr_type_id: int
    pqr_type_name: str | None = None
    priority_id: int
    priority_name: str | None = None
    pqr_status_id: int
    pqr_status_name: str | None = None
    subject: str
    description: str
    resolution: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class PqrCommentCreate(BaseModel):
    comment: str


class PqrCommentOut(BaseModel):
    id: int
    pqr_id: UUID
    user_id: UUID
    user_name: str | None = None
    comment: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
