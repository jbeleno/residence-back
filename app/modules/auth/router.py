"""Auth router – login with PIN, password reset, email verification."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, oauth2_scheme
from app.core.responses import success
from app.core.security import decode_access_token
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.schemas.auth import (
    ChangePasswordRequest,
    ConfirmEmailChange,
    LoginRequest,
    RequestEmailChange,
    RequestPasswordResetRequest,
    RequestPinRequest,
    ResetPasswordRequest,
    SelectCondominiumRequest,
    VerifyEmailRequest,
    VerifyLoginPinRequest,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(AuthRepository(db))


# ══════════════════════════════════════════════════════════════════════════
#  Login (2-step with PIN)
# ══════════════════════════════════════════════════════════════════════════

@router.post("/login")
async def login_step1(body: LoginRequest, svc: AuthService = Depends(_service)):
    """Validate credentials and return JWT directly."""
    data = await svc.login_step1(body)
    return success(data.model_dump())


@router.post("/login/verify-pin")
async def login_step2(body: VerifyLoginPinRequest, svc: AuthService = Depends(_service)):
    """Step 2: verify PIN → issue JWT."""
    data = await svc.login_step2(body)
    return success(data.model_dump())


# ══════════════════════════════════════════════════════════════════════════
#  Password reset
# ══════════════════════════════════════════════════════════════════════════

@router.post("/forgot-password")
async def forgot_password(body: RequestPasswordResetRequest, svc: AuthService = Depends(_service)):
    """Request a password-reset PIN via email."""
    data = await svc.request_password_reset(body)
    return success(data)


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, svc: AuthService = Depends(_service)):
    """Verify PIN and set new password."""
    data = await svc.reset_password(body)
    return success(data)


# ══════════════════════════════════════════════════════════════════════════
#  Email / account verification
# ══════════════════════════════════════════════════════════════════════════

@router.post("/request-verify-email")
async def request_verify_email(body: RequestPinRequest, svc: AuthService = Depends(_service)):
    """Send account-verification PIN to email."""
    data = await svc.request_verify_email(body)
    return success(data)


@router.post("/verify-email")
async def verify_email(body: VerifyEmailRequest, svc: AuthService = Depends(_service)):
    """Verify email PIN → mark account as verified."""
    data = await svc.verify_email(body)
    return success(data)


# ══════════════════════════════════════════════════════════════════════════
#  Existing endpoints
# ══════════════════════════════════════════════════════════════════════════

@router.post("/select-condominium")
async def select_condominium(
    body: SelectCondominiumRequest,
    token: str = Depends(oauth2_scheme),
    svc: AuthService = Depends(_service),
):
    payload = decode_access_token(token)
    if payload is None:
        from app.core.exceptions import UnauthorizedError
        raise UnauthorizedError("Token inválido")
    data = await svc.select_condominium(body, payload["sub"])
    return success(data.model_dump())


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    svc: AuthService = Depends(_service),
):
    await svc.change_password(current_user.id, body)
    return success({"message": "Contraseña actualizada exitosamente"})


@router.get("/me")
async def get_me(
    current_user=Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
    svc: AuthService = Depends(_service),
):
    data = await svc.get_me(current_user, token)
    return success(data.model_dump())


@router.post("/me/email/request")
async def request_email_change(
    body: RequestEmailChange,
    current_user=Depends(get_current_user),
    svc: AuthService = Depends(_service),
):
    """Request an email change PIN sent to the new email."""
    data = await svc.request_email_change(current_user, body)
    return success(data)


@router.post("/me/email/confirm")
async def confirm_email_change(
    body: ConfirmEmailChange,
    current_user=Depends(get_current_user),
    svc: AuthService = Depends(_service),
):
    """Confirm email change with PIN."""
    data = await svc.confirm_email_change(current_user, body)
    return success(data)
