"""Auth service – business logic with PIN-based email verification."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from app.core.audit import log_event
from app.core.config import settings
from app.core.email import generate_pin, send_pin_email

logger = logging.getLogger(__name__)
from app.core.exceptions import BadRequestError, ForbiddenError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.repository import AuthRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    CondominiumRoleOut,
    ConfirmEmailChange,
    LoginDataOut,
    LoginRequest,
    RequestEmailChange,
    RequestPasswordResetRequest,
    RequestPinRequest,
    ResetPasswordRequest,
    SelectCondominiumRequest,
    TokenResponse,
    UserPropertyOut,
    VerifyEmailRequest,
    VerifyLoginPinRequest,
)
from app.core.exceptions import ConflictError


class AuthService:
    def __init__(self, repo: AuthRepository) -> None:
        self._repo = repo

    # ── helpers ────────────────────────────────────────────────────────────

    async def _send_pin(
        self, email: str, pin_type: str, *, silent_on_missing: bool = False,
    ) -> dict:
        """Generate a PIN for the user and email it.

        If silent_on_missing=True and the email is not registered, returns the
        same generic message without revealing the user's existence (used for
        password reset to avoid email enumeration).

        SMTP failures are logged but never raised — the PIN is stored in the
        DB regardless and surfaced via logs in DEBUG.
        """
        generic_msg = (
            f"Si el correo está registrado, recibirás un código. "
            f"Expira en {settings.PIN_EXPIRE_MINUTES} minutos."
        )

        user = await self._repo.get_user_by_email(email)
        if user is None:
            if silent_on_missing:
                return {"message": generic_msg}
            raise UnauthorizedError("Correo no registrado")

        await self._repo.invalidate_existing_pins(user.id, pin_type)

        pin = generate_pin()
        expires = datetime.utcnow() + timedelta(minutes=settings.PIN_EXPIRE_MINUTES)
        await self._repo.create_pin(user.id, pin, pin_type, expires)
        await self._repo.save()

        # Always log the PIN in DEBUG so devs can recover when SMTP isn't set up.
        if settings.DEBUG:
            logger.warning("🔑 [DEV] PIN for %s (%s): %s", email, pin_type, pin)

        # Try to send via SMTP. Don't fail the request if the mail server is
        # down — the PIN is already persisted; surface the failure in logs.
        try:
            send_pin_email(user.email, pin, pin_type, user.full_name)
        except Exception:
            logger.exception("SMTP failed to send %s PIN to %s", pin_type, email)

        if silent_on_missing:
            return {"message": generic_msg}
        return {
            "message": f"Código enviado a {email}. Expira en {settings.PIN_EXPIRE_MINUTES} minutos.",
        }

    async def _verify_pin(self, email: str, pin_code: str, pin_type: str):
        user = await self._repo.get_user_by_email(email)
        if user is None:
            raise UnauthorizedError("Correo no registrado")

        pin = await self._repo.get_valid_pin(user.id, pin_code, pin_type)
        if pin is None:
            raise BadRequestError("Código inválido o expirado")

        await self._repo.mark_pin_used(pin)
        return user

    # ══════════════════════════════════════════════════════════════════════
    #  FLOW 1 – Login with PIN (2-step)
    # ══════════════════════════════════════════════════════════════════════

    async def login_step1(self, body: LoginRequest) -> LoginDataOut:
        """Validate credentials and issue JWT directly."""
        user = await self._repo.get_user_by_email(body.email)
        if user is None or not verify_password(body.password, user.password_hash):
            await log_event(
                self._repo._db, "LOGIN_FAILED",
                metadata={"email": body.email, "reason": "bad_credentials"},
            )
            await self._repo.save()
            raise UnauthorizedError("Credenciales inválidas")
        if not user.is_active:
            await log_event(
                self._repo._db, "LOGIN_FAILED",
                user_id=user.id, user_email=user.email,
                metadata={"reason": "inactive_user"},
            )
            await self._repo.save()
            raise ForbiddenError("Usuario inactivo")

        user.last_login_at = datetime.utcnow()
        await log_event(
            self._repo._db, "LOGIN_SUCCESS",
            user_id=user.id, user_email=user.email,
            metadata={"flow": "password"},
        )
        await self._repo.save()

        ucr_rows = await self._repo.get_user_condominium_roles(user.id)
        condominiums = [
            CondominiumRoleOut(
                condominium_id=condo.id,
                condominium_name=condo.name,
                role=role.role_name,
            )
            for _ucr, condo, role in ucr_rows
        ]

        prop_rows = await self._repo.get_user_properties(user.id)
        properties = [
            UserPropertyOut(
                property_id=prop.id,
                property_number=prop.number,
                block=prop.block,
                condominium_id=prop.condominium_id,
            )
            for _up, prop in prop_rows
        ]

        access_token: str | None = None
        message: str | None = None

        if len(condominiums) == 1:
            c = condominiums[0]
            access_token = create_access_token(
                {"sub": str(user.id), "cid": str(c.condominium_id), "role": c.role}
            )
        elif len(condominiums) > 1:
            access_token = create_access_token({"sub": str(user.id)})
            message = "Seleccione un condominio para continuar."
        else:
            access_token = create_access_token({"sub": str(user.id)})
            message = "No tiene condominios asignados. Contacte al administrador."

        return LoginDataOut(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            condominiums=condominiums,
            properties=properties,
            access_token=access_token,
            message=message,
        )

    async def login_step2(self, body: VerifyLoginPinRequest) -> LoginDataOut:
        """Verify login PIN and issue JWT."""
        user = await self._verify_pin(body.email, body.pin, "login")
        if not user.is_active:
            raise ForbiddenError("Usuario inactivo")

        user.last_login_at = datetime.utcnow()
        await self._repo.save()

        ucr_rows = await self._repo.get_user_condominium_roles(user.id)
        condominiums = [
            CondominiumRoleOut(
                condominium_id=condo.id,
                condominium_name=condo.name,
                role=role.role_name,
            )
            for _ucr, condo, role in ucr_rows
        ]

        prop_rows = await self._repo.get_user_properties(user.id)
        properties = [
            UserPropertyOut(
                property_id=prop.id,
                property_number=prop.number,
                block=prop.block,
                condominium_id=prop.condominium_id,
            )
            for _up, prop in prop_rows
        ]

        access_token: str | None = None
        message: str | None = None

        if len(condominiums) == 1:
            c = condominiums[0]
            access_token = create_access_token(
                {"sub": str(user.id), "cid": str(c.condominium_id), "role": c.role}
            )
        elif len(condominiums) > 1:
            access_token = create_access_token({"sub": str(user.id)})
            message = "Seleccione un condominio para continuar."
        else:
            access_token = create_access_token({"sub": str(user.id)})
            message = "No tiene condominios asignados. Contacte al administrador."

        return LoginDataOut(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            condominiums=condominiums,
            properties=properties,
            access_token=access_token,
            message=message,
        )

    # ══════════════════════════════════════════════════════════════════════
    #  FLOW 2 – Password reset
    # ══════════════════════════════════════════════════════════════════════

    async def request_password_reset(self, body: RequestPasswordResetRequest) -> dict:
        # silent_on_missing avoids leaking which emails are registered.
        return await self._send_pin(body.email, "reset_password", silent_on_missing=True)

    async def reset_password(self, body: ResetPasswordRequest) -> dict:
        user = await self._verify_pin(body.email, body.pin, "reset_password")
        user.password_hash = hash_password(body.new_password)
        await self._repo.save()
        return {"message": "Contraseña restablecida exitosamente. Inicie sesión."}

    # ══════════════════════════════════════════════════════════════════════
    #  FLOW 3 – Email / account verification
    # ══════════════════════════════════════════════════════════════════════

    async def request_verify_email(self, body: RequestPinRequest) -> dict:
        return await self._send_pin(body.email, "verify_email")

    async def verify_email(self, body: VerifyEmailRequest) -> dict:
        user = await self._verify_pin(body.email, body.pin, "verify_email")
        user.email_verified = True
        await self._repo.save()
        return {"message": "Correo verificado exitosamente."}

    # ══════════════════════════════════════════════════════════════════════
    #  Existing flows (unchanged)
    # ══════════════════════════════════════════════════════════════════════

    async def select_condominium(
        self, body: SelectCondominiumRequest, user_id: str
    ) -> TokenResponse:
        row = await self._repo.get_user_role_in_condominium(
            user_id, body.condominium_id
        )
        if row is None:
            raise ForbiddenError("No pertenece a este condominio")
        _ucr, role = row

        new_token = create_access_token(
            {"sub": user_id, "cid": str(body.condominium_id), "role": role.role_name}
        )
        return TokenResponse(access_token=new_token)

    async def change_password(
        self, user_id, body: ChangePasswordRequest
    ) -> None:
        user = await self._repo.get_user_by_id(user_id)
        if user is None:
            raise UnauthorizedError("Usuario no encontrado")
        if not verify_password(body.current_password, user.password_hash):
            await log_event(
                self._repo._db, "PASSWORD_CHANGE_FAILED",
                user_id=user.id, user_email=user.email,
                metadata={"reason": "bad_current_password"},
            )
            await self._repo.save()
            raise BadRequestError("Contraseña actual incorrecta")
        user.password_hash = hash_password(body.new_password)
        await log_event(
            self._repo._db, "PASSWORD_CHANGED",
            user_id=user.id, user_email=user.email,
        )
        await self._repo.save()

    async def get_me(self, user, token: str) -> LoginDataOut:
        ucr_rows = await self._repo.get_user_condominium_roles(user.id)
        condominiums = [
            CondominiumRoleOut(
                condominium_id=condo.id,
                condominium_name=condo.name,
                role=role.role_name,
            )
            for _ucr, condo, role in ucr_rows
        ]
        prop_rows = await self._repo.get_user_properties(user.id)
        properties = [
            UserPropertyOut(
                property_id=prop.id,
                property_number=prop.number,
                block=prop.block,
                condominium_id=prop.condominium_id,
            )
            for _up, prop in prop_rows
        ]
        return LoginDataOut(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            condominiums=condominiums,
            properties=properties,
            access_token=token,
        )

    # ══════════════════════════════════════════════════════════════════════
    #  Email change (self-service with PIN)
    # ══════════════════════════════════════════════════════════════════════

    async def request_email_change(self, user, body: RequestEmailChange) -> dict:
        """Send a PIN to the new email address."""
        existing = await self._repo.get_user_by_email(body.new_email)
        if existing is not None and existing.id != user.id:
            raise ConflictError("Ese correo ya está registrado por otro usuario")
        if existing is not None and existing.id == user.id:
            raise BadRequestError("Ese ya es tu correo actual")

        await self._repo.invalidate_existing_pins(user.id, "change_email")

        pin = generate_pin()
        expires = datetime.utcnow() + timedelta(minutes=settings.PIN_EXPIRE_MINUTES)
        await self._repo.create_pin(
            user.id, pin, "change_email", expires, payload=body.new_email,
        )
        await self._repo.save()

        if settings.DEBUG:
            logger.warning("🔑 [DEV] PIN change_email for %s -> %s: %s",
                           user.email, body.new_email, pin)
        try:
            send_pin_email(body.new_email, pin, "change_email", user.full_name)
        except Exception:
            logger.exception("SMTP failed to send change_email PIN to %s", body.new_email)

        return {
            "message": f"Código enviado a {body.new_email}. Expira en {settings.PIN_EXPIRE_MINUTES} minutos.",
        }

    async def confirm_email_change(self, user, body: ConfirmEmailChange) -> dict:
        """Verify PIN and update user email."""
        pin = await self._repo.get_valid_pin(user.id, body.pin, "change_email")
        if pin is None:
            raise BadRequestError("Código inválido o expirado")
        if not pin.payload:
            raise BadRequestError("Solicitud de cambio inválida")

        old_email = user.email
        user.email = pin.payload
        user.email_verified = True
        await self._repo.mark_pin_used(pin)
        await log_event(
            self._repo._db, "EMAIL_CHANGED",
            user_id=user.id, user_email=user.email,
            metadata={"from": old_email, "to": pin.payload},
        )
        await self._repo.save()
        return {"message": "Correo actualizado exitosamente."}
