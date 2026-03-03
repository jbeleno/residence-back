"""User schemas."""

from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    phone_secondary: str | None = None
    document_type_id: int | None = None
    document_number: str | None = None
    avatar_url: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_relation: str | None = None


class UserCreate(UserBase):
    password: str
    condominium_id: UUID | None = None
    role_id: int | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    phone_secondary: str | None = None
    document_type_id: int | None = None
    document_number: str | None = None
    avatar_url: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_relation: str | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone: str | None = None
    phone_secondary: str | None = None
    document_type_id: int | None = None
    document_number: str | None = None
    avatar_url: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_relation: str | None = None
    email_verified: bool = False
    is_active: bool = True
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserDeviceCreate(BaseModel):
    device_token: str
    device_type: str
    device_name: str | None = None


class UserDeviceOut(BaseModel):
    id: int
    device_token: str
    device_type: str
    device_name: str | None = None
    is_active: bool = True
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
