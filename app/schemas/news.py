"""News schemas."""

from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class NewsCreate(BaseModel):
    title: str
    content: str
    is_pinned: bool = False
    is_published: bool = True
    publish_date: datetime | None = None
    expires_at: datetime | None = None


class NewsUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    is_pinned: bool | None = None
    is_published: bool | None = None
    expires_at: datetime | None = None


class NewsOut(BaseModel):
    id: int
    condominium_id: UUID
    author_id: UUID
    author_name: str | None = None
    title: str
    content: str
    is_pinned: bool = False
    is_published: bool = True
    publish_date: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
