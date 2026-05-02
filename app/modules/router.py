"""Central API router – aggregates all module routers under /api/v1."""

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.catalogs.router import router as catalogs_router
from app.modules.condominiums.router import router as condominiums_router
from app.modules.users.router import router as users_router
from app.modules.properties.router import router as properties_router
from app.modules.amenities.router import router as amenities_router
from app.modules.finance.router import router as finance_router
from app.modules.visitors.router import router as visitors_router
from app.modules.parking.router import router as parking_router
from app.modules.pets.router import router as pets_router
from app.modules.news.router import router as news_router
from app.modules.pqrs.router import router as pqrs_router
from app.modules.notifications.router import router as notifications_router
from app.modules.chatbot.router import router as chatbot_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.uploads.router import router as uploads_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(catalogs_router)
api_router.include_router(condominiums_router)
api_router.include_router(users_router)
api_router.include_router(properties_router)
api_router.include_router(amenities_router)
api_router.include_router(finance_router)
api_router.include_router(visitors_router)
api_router.include_router(parking_router)
api_router.include_router(pets_router)
api_router.include_router(news_router)
api_router.include_router(pqrs_router)
api_router.include_router(notifications_router)
api_router.include_router(chatbot_router)
api_router.include_router(dashboard_router)
api_router.include_router(uploads_router)
