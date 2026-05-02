"""Audit infrastructure.

Three pieces:

1. ``AuditContext`` — a ``contextvars.ContextVar`` populated by the FastAPI
   middleware on every request. Holds the current user_id, role, condo_id,
   IP, user-agent, method, path. The SQLAlchemy event listener reads from
   here so it knows *who* made the change.

2. SQLAlchemy ``before_flush`` event listener — runs once per session flush
   and turns every dirty / new / deleted ORM instance (except in
   ``EXCLUDED_TABLES``) into an ``AuditLog`` row that gets inserted in the
   same transaction.

3. ``log_event`` helper — fire-and-forget for events that aren't tied to a
   model change (login success, login failure, password change attempt,
   email change request, etc.). The caller passes a session and the helper
   adds the AuditLog row to it.

Sensitive fields are redacted before being persisted in ``changes``.
"""

from __future__ import annotations

import contextvars
import logging
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


# ── Context ──────────────────────────────────────────────────────────────


class AuditContext:
    __slots__ = (
        "user_id", "user_email", "user_role", "condominium_id",
        "ip_address", "user_agent", "method", "path",
    )

    def __init__(
        self,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        condominium_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
    ) -> None:
        self.user_id = user_id
        self.user_email = user_email
        self.user_role = user_role
        self.condominium_id = condominium_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.method = method
        self.path = path


_current: contextvars.ContextVar[Optional[AuditContext]] = contextvars.ContextVar(
    "audit_context", default=None,
)


def set_context(ctx: AuditContext) -> contextvars.Token:
    return _current.set(ctx)


def get_context() -> Optional[AuditContext]:
    return _current.get()


def reset_context(token: contextvars.Token) -> None:
    _current.reset(token)


# ── Redaction ────────────────────────────────────────────────────────────

SENSITIVE_FIELDS = {
    "password", "password_hash", "pin_code", "device_token",
    "secret", "secret_access_key", "smtp_password", "api_key",
    "authorization", "token", "access_token", "refresh_token",
    "payload",  # email_pins.payload often holds the new email or other secrets
}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: ("***REDACTED***" if k.lower() in SENSITIVE_FIELDS else _redact(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


# ── Tables we never audit ────────────────────────────────────────────────

EXCLUDED_TABLES = {
    "audit_logs",         # avoid recursion
    "email_pins",         # contains PINs
    "document_chunks",    # massive embeddings
    "chat_messages",      # noisy conversational data
    "chat_sessions",      # ditto
    "notifications",      # high-volume read-side
}


# Map model __tablename__ → singular entity_type label for nicer logs
ENTITY_LABELS = {
    "users": "user",
    "condominiums": "condominium",
    "properties": "property",
    "user_condominium_roles": "user_role",
    "user_properties": "user_property",
    "amenities": "amenity",
    "amenity_bookings": "booking",
    "invoices": "invoice",
    "payments": "payment",
    "charge_types": "charge_type",
    "vehicles": "vehicle",
    "pets": "pet",
    "pqrs": "pqr",
    "pqr_comments": "pqr_comment",
    "news_board": "news",
    "visitor_logs": "visitor_log",
    "parking_spaces": "parking_space",
    "visitor_parking": "visitor_parking",
    "documents": "kb_document",
    "user_devices": "device",
    "roles": "role",
}


# ── Diff helpers ─────────────────────────────────────────────────────────


def _value_for_log(v: Any) -> Any:
    """Convert ORM-friendly types to JSON-friendly ones."""
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, UUID):
        return str(v)
    # datetime, date, time — isoformat handled by SQLAlchemy JSONB serializer,
    # but we cast to str defensively.
    return str(v)


def _snapshot(instance: Any) -> dict[str, Any]:
    """Return a JSON-safe dict of all column values on the instance."""
    out: dict[str, Any] = {}
    mapper = inspect(instance.__class__)
    for col in mapper.columns:
        out[col.key] = _value_for_log(getattr(instance, col.key, None))
    return _redact(out)


def _diff(instance: Any) -> dict[str, dict[str, Any]]:
    """For a dirty (UPDATE'd) instance, return {column: {old, new}}."""
    out: dict[str, dict[str, Any]] = {}
    state = inspect(instance)
    for attr in state.attrs:
        hist = attr.history
        if not hist.has_changes():
            continue
        # has_changes() can be true also for relationship loads; restrict to columns
        if attr.key not in {c.key for c in inspect(instance.__class__).columns}:
            continue
        old = hist.deleted[0] if hist.deleted else None
        new = hist.added[0] if hist.added else getattr(instance, attr.key, None)
        out[attr.key] = {"old": _value_for_log(old), "new": _value_for_log(new)}
    return _redact(out)


def _entity_id(instance: Any) -> Optional[str]:
    pk = inspect(instance).identity
    if pk is None:
        # New instance — id may be auto-assigned after flush. Try direct attr.
        for col in inspect(instance.__class__).primary_key:
            v = getattr(instance, col.key, None)
            if v is not None:
                return str(v)
        return None
    if len(pk) == 1:
        return str(pk[0])
    return ",".join(str(p) for p in pk)


def _condo_id(instance: Any) -> Optional[UUID]:
    return getattr(instance, "condominium_id", None)


# ── before_flush listener ────────────────────────────────────────────────


def _build_log(action: str, instance: Any, ctx: Optional[AuditContext]) -> AuditLog:
    table = instance.__tablename__
    entity_type = ENTITY_LABELS.get(table, table)

    if action == "CREATE":
        changes = _snapshot(instance)
    elif action == "UPDATE":
        changes = _diff(instance)
    else:  # DELETE
        changes = _snapshot(instance)

    log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=_entity_id(instance),
        changes=changes,
        condominium_id=_condo_id(instance),
    )
    if ctx is not None:
        log.user_id = ctx.user_id
        log.user_email = ctx.user_email
        log.user_role = ctx.user_role
        # If the instance has its own condo, prefer that; otherwise use ctx.
        if log.condominium_id is None:
            log.condominium_id = ctx.condominium_id
        log.ip_address = ctx.ip_address
        log.user_agent = (ctx.user_agent or "")[:500] or None
        log.method = ctx.method
        log.path = (ctx.path or "")[:500] or None
    return log


def _on_before_flush(session: Session, flush_context, instances) -> None:  # noqa: ARG001
    """Capture every pending change as an AuditLog row in the same transaction."""
    ctx = get_context()
    new_logs: list[AuditLog] = []

    for obj in list(session.new):
        if obj.__tablename__ in EXCLUDED_TABLES:
            continue
        try:
            new_logs.append(_build_log("CREATE", obj, ctx))
        except Exception:
            logger.exception("audit: failed to build CREATE log for %s", type(obj))

    for obj in list(session.dirty):
        if obj.__tablename__ in EXCLUDED_TABLES:
            continue
        if not session.is_modified(obj, include_collections=False):
            continue
        try:
            diff = _diff(obj)
            if not diff:
                continue
            log = _build_log("UPDATE", obj, ctx)
            log.changes = diff
            new_logs.append(log)
        except Exception:
            logger.exception("audit: failed to build UPDATE log for %s", type(obj))

    for obj in list(session.deleted):
        if obj.__tablename__ in EXCLUDED_TABLES:
            continue
        try:
            new_logs.append(_build_log("DELETE", obj, ctx))
        except Exception:
            logger.exception("audit: failed to build DELETE log for %s", type(obj))

    for log in new_logs:
        session.add(log)


def install_listener() -> None:
    """Wire the before_flush listener once at app startup."""
    from app.core.database import async_session_factory

    # async_sessionmaker exposes the underlying sync Session class via .sync_session_class
    # but in SQLAlchemy 2.x async sessions emit ORM events on the underlying Session.
    # Listening on Session globally covers all sessions.
    if not getattr(install_listener, "_installed", False):
        event.listen(Session, "before_flush", _on_before_flush)
        install_listener._installed = True  # type: ignore[attr-defined]


# ── Manual log helper ────────────────────────────────────────────────────


async def log_event(
    db,
    action: str,
    *,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    user_id: Optional[UUID] = None,
    user_email: Optional[str] = None,
    user_role: Optional[str] = None,
    condominium_id: Optional[UUID] = None,
) -> None:
    """Fire-and-forget event log for things that aren't a row change.

    Examples: LOGIN_SUCCESS, LOGIN_FAILED, PASSWORD_RESET_REQUEST,
    EMAIL_CHANGE_REQUEST, EMAIL_CHANGE_CONFIRM, USER_LOGGED_OUT.

    The caller decides on persistence — this just adds to the session.
    """
    ctx = get_context()
    log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        extra_metadata=_redact(metadata) if metadata else None,
    )
    log.user_id = user_id or (ctx.user_id if ctx else None)
    log.user_email = user_email or (ctx.user_email if ctx else None)
    log.user_role = user_role or (ctx.user_role if ctx else None)
    log.condominium_id = condominium_id or (ctx.condominium_id if ctx else None)
    if ctx is not None:
        log.ip_address = ctx.ip_address
        log.user_agent = (ctx.user_agent or "")[:500] or None
        log.method = ctx.method
        log.path = (ctx.path or "")[:500] or None

    db.add(log)
