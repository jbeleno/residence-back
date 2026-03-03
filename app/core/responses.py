"""Unified JSON response helpers.

Every API response follows the contract:
    {
      "status": "success" | "error",
      "data": <T> | [],
      "meta": { "page": 1, "total": 100 },   // listados
      "error": { "code": "...", "message": "..." }  // solo errores
    }
"""

from __future__ import annotations

from typing import Any, Generic, Optional, Sequence, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Meta ──────────────────────────────────────────────────────────────────


class PaginationMeta(BaseModel):
    page: int = 1
    page_size: int = 50
    total: int = 0


# ── Unified response wrappers ────────────────────────────────────────────


class SuccessResponse(BaseModel, Generic[T]):
    status: str = "success"
    data: T
    meta: Optional[PaginationMeta] = None


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    status: str = "error"
    data: None = None
    error: ErrorBody


# ── Helper factories ─────────────────────────────────────────────────────


def success(data: Any, *, meta: Optional[PaginationMeta] = None) -> dict[str, Any]:
    """Build a dict following the unified contract (for direct ``return``)."""
    body: dict[str, Any] = {"status": "success", "data": data}
    if meta is not None:
        body["meta"] = meta.model_dump()
    return body


def success_list(
    items: Sequence[Any],
    *,
    total: int,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    return success(
        items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


# ── Pagination query params dependency ───────────────────────────────────


class PaginationParams(BaseModel):
    """Inject via ``Depends()`` on route signatures."""
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
