"""Dashboard router."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_condominium_id, require_admin
from app.core.responses import success
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(DashboardRepository(db))


@router.get("/summary", dependencies=[Depends(require_admin)])
async def dashboard_summary(
    cid: UUID = Depends(get_current_condominium_id),
    svc: DashboardService = Depends(_service),
):
    return success(await svc.summary(cid))
