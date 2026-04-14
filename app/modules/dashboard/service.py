"""Dashboard service – assembles the admin summary payload."""

from __future__ import annotations

from uuid import UUID

from app.modules.dashboard.repository import DashboardRepository


class DashboardService:
    def __init__(self, repo: DashboardRepository) -> None:
        self._repo = repo

    async def summary(self, cid: UUID) -> dict:
        total_units = await self._repo.count_properties(cid)
        active_residents = await self._repo.count_active_residents(cid)
        pending_payments = await self._repo.pending_payments_total(cid)
        open_pqrs = await self._repo.count_open_pqrs(cid)
        visitors = await self._repo.active_visitors(cid)
        monthly = await self._repo.monthly_collections(cid)

        return {
            "stats": {
                "total_units": total_units,
                "active_residents": active_residents,
                "pending_payments": pending_payments,
                "open_pqrs": open_pqrs,
            },
            "active_visitors": [
                {
                    "id": str(v.id),
                    "visitor_name": v.visitor_name,
                    "property_number": v.property.number if v.property else None,
                    "entry_time": v.entry_time.isoformat() if v.entry_time else None,
                    "is_guest": v.is_guest,
                    "vehicle_plate": v.vehicle_plate,
                    "notes": v.notes,
                }
                for v in visitors
            ],
            "monthly_collections": monthly,
        }
