"""Auth schemas."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SelectCondominiumRequest(BaseModel):
    condominium_id: UUID


class CondominiumRoleOut(BaseModel):
    condominium_id: UUID
    condominium_name: str
    role: str


class UserPropertyOut(BaseModel):
    property_id: UUID
    property_number: str
    block: str | None = None
    condominium_id: UUID


class LoginDataOut(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    phone: str | None = None
    condominiums: list[CondominiumRoleOut] = []
    properties: list[UserPropertyOut] = []
    access_token: str | None = None
    message: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ── PIN-based flows ───────────────────────────────────────────────────────

class RequestPinRequest(BaseModel):
    """Used for login-pin and verify-email flows."""
    email: EmailStr
    pin_type: str = "login"  # login | verify_email


class VerifyLoginPinRequest(BaseModel):
    email: EmailStr
    pin: str


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    pin: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    pin: str


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: str | None = None
    condominium_id: UUID | None = None
