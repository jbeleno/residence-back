"""Application entry point – FastAPI factory with CORS, exception handlers, and router wiring."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.audit import AuditContext, install_listener, reset_context, set_context
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import setup_logging
from app.core.security import decode_access_token
from app.modules.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(debug=settings.DEBUG)
    install_listener()  # audit: hook before_flush once
    logger.info("Residence API starting – debug=%s", settings.DEBUG)
    yield
    logger.info("Residence API shutting down")


async def _audit_middleware(request: Request, call_next):
    """Populate the audit ContextVar for the duration of the request."""
    from uuid import UUID

    user_id = None
    role = None
    cid = None

    # Best-effort extract from JWT if present (don't fail the request on bad tokens here;
    # the protected endpoints' own deps will raise 401).
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
        payload = decode_access_token(token)
        if payload:
            try:
                user_id = UUID(payload["sub"]) if payload.get("sub") else None
            except Exception:
                user_id = None
            role = payload.get("role")
            try:
                cid = UUID(payload["cid"]) if payload.get("cid") else None
            except Exception:
                cid = None

    # Pull client IP — respect X-Forwarded-For when behind nginx
    fwd = request.headers.get("x-forwarded-for")
    ip = (fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else None))

    ctx = AuditContext(
        user_id=user_id,
        user_role=role,
        condominium_id=cid,
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
        method=request.method,
        path=request.url.path,
    )
    token = set_context(ctx)
    try:
        return await call_next(request)
    finally:
        reset_context(token)


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # ── Audit context (must run BEFORE CORS so it wraps every request) ─
    application.middleware("http")(_audit_middleware)

    # ── CORS ──────────────────────────────────────────────────────────
    origins = settings.cors_origins_list
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Health check ──────────────────────────────────────────────────
    @application.get("/health", tags=["health"])
    async def health():
        return JSONResponse({"status": "ok"})

    register_exception_handlers(application)
    application.include_router(api_router)

    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
