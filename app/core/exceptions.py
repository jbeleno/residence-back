"""Custom exception hierarchy and FastAPI exception handlers.

Every domain error inherits from ``AppException`` and carries:
    * ``status_code``  – HTTP status (default 400)
    * ``code``         – machine-readable string (e.g. ``"ENTITY_NOT_FOUND"``)
    * ``message``      – human-readable description (Spanish by convention)
"""

from __future__ import annotations

import logging
import traceback
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ── Base ──────────────────────────────────────────────────────────────────


class AppException(Exception):
    """Base for all application-level errors."""

    status_code: int = 400
    code: str = "APP_ERROR"
    message: str = "Error inesperado"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
        detail: Any = None,
    ) -> None:
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


# ── Concrete exceptions ──────────────────────────────────────────────────


class BadRequestError(AppException):
    status_code = 400
    code = "BAD_REQUEST"
    message = "Solicitud inválida"


class UnauthorizedError(AppException):
    status_code = 401
    code = "UNAUTHORIZED"
    message = "No autenticado"


class ForbiddenError(AppException):
    status_code = 403
    code = "FORBIDDEN"
    message = "No tiene permisos para realizar esta acción"


class NotFoundError(AppException):
    status_code = 404
    code = "NOT_FOUND"
    message = "Recurso no encontrado"


class ConflictError(AppException):
    status_code = 409
    code = "CONFLICT"
    message = "El recurso ya existe o hay un conflicto de datos"


class TenantAccessError(ForbiddenError):
    code = "TENANT_ACCESS_DENIED"
    message = "No tiene acceso a datos de este condominio"


class InternalError(AppException):
    status_code = 500
    code = "INTERNAL_ERROR"
    message = "Error interno del servidor"


# ── Handler registration ─────────────────────────────────────────────────


def _build_error_body(exc: AppException) -> dict[str, Any]:
    return {
        "status": "error",
        "data": None,
        "error": {
            "code": exc.code,
            "message": exc.message,
        },
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Attach custom exception handlers to the FastAPI application."""

    @app.exception_handler(AppException)
    async def handle_app_exception(_req: Request, exc: AppException) -> JSONResponse:
        logger.warning("AppException %s: %s", exc.code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_body(exc),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_req: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning("Validation error: %s", exc.errors())
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "data": None,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Error de validación en los datos enviados",
                    "details": exc.errors(),
                },
            },
        )

    @app.exception_handler(Exception)
    async def handle_unhandled(_req: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception: %s\n%s", exc, traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "data": None,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Error interno del servidor",
                },
            },
        )
