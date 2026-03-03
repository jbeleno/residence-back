"""Shared / cross-cutting Pydantic schemas."""

from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class MessageResponse(BaseModel):
    message: str
