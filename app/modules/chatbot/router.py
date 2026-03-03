"""Chatbot router – RAG chat, document management, and legacy summaries."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    get_current_condominium_id,
    get_current_user,
    require_admin,
    require_authenticated,
)
from app.core.responses import success
from app.modules.chatbot.repository import ChatbotRepository
from app.modules.chatbot.service import ChatbotService

router = APIRouter(prefix="/chatbot", tags=["Chatbot IA"])


def _service(db: AsyncSession = Depends(get_db)) -> ChatbotService:
    return ChatbotService(ChatbotRepository(db))


# ── Request schemas ───────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None


class DocumentTextRequest(BaseModel):
    title: str
    content: str


# ══════════════════════════════════════════════════════════════════════════
#  AI Chat (RAG)
# ══════════════════════════════════════════════════════════════════════════

@router.post("/chat")
async def chat(
    body: ChatRequest,
    current_user=Depends(get_current_user),
    cid: UUID = Depends(get_current_condominium_id),
    svc: ChatbotService = Depends(_service),
):
    """Send a message to the AI chatbot. Creates a new session if session_id is not provided."""
    data = await svc.chat(cid, current_user.id, body.session_id, body.message)
    return success(data)


# ══════════════════════════════════════════════════════════════════════════
#  Chat sessions
# ══════════════════════════════════════════════════════════════════════════

@router.get("/sessions")
async def list_sessions(
    current_user=Depends(get_current_user),
    cid: UUID = Depends(get_current_condominium_id),
    svc: ChatbotService = Depends(_service),
):
    data = await svc.list_sessions(current_user.id, cid)
    return success(data)


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    current_user=Depends(get_current_user),
    svc: ChatbotService = Depends(_service),
):
    data = await svc.get_session_messages(session_id, current_user.id)
    return success(data)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user=Depends(get_current_user),
    svc: ChatbotService = Depends(_service),
):
    data = await svc.delete_session(session_id, current_user.id)
    return success(data)


# ══════════════════════════════════════════════════════════════════════════
#  Document management (admin only)
# ══════════════════════════════════════════════════════════════════════════

@router.post("/documents", dependencies=[Depends(require_admin)])
async def upload_document_text(
    body: DocumentTextRequest,
    current_user=Depends(get_current_user),
    cid: UUID = Depends(get_current_condominium_id),
    svc: ChatbotService = Depends(_service),
):
    """Upload a text document to the knowledge base."""
    data = await svc.upload_document(cid, current_user.id, body.title, body.content)
    return success(data)


@router.post("/documents/upload", dependencies=[Depends(require_admin)])
async def upload_document_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    current_user=Depends(get_current_user),
    cid: UUID = Depends(get_current_condominium_id),
    svc: ChatbotService = Depends(_service),
):
    """Upload a .txt file to the knowledge base."""
    content = (await file.read()).decode("utf-8", errors="ignore")
    data = await svc.upload_document(
        cid, current_user.id, title, content,
        source_type="file", filename=file.filename,
    )
    return success(data)


@router.get("/documents", dependencies=[Depends(require_admin)])
async def list_documents(
    cid: UUID = Depends(get_current_condominium_id),
    svc: ChatbotService = Depends(_service),
):
    data = await svc.list_documents(cid)
    return success(data)


@router.delete("/documents/{doc_id}", dependencies=[Depends(require_admin)])
async def delete_document(
    doc_id: int,
    cid: UUID = Depends(get_current_condominium_id),
    svc: ChatbotService = Depends(_service),
):
    data = await svc.delete_document(doc_id, cid)
    return success(data)


# ══════════════════════════════════════════════════════════════════════════
#  Legacy summary endpoints (backward compatible)
# ══════════════════════════════════════════════════════════════════════════

@router.get("/condominium-info", dependencies=[Depends(require_authenticated)])
async def condominium_info(
    cid: UUID = Depends(get_current_condominium_id),
    svc: ChatbotService = Depends(_service),
):
    return success(await svc.condominium_info(cid))


@router.get("/amenities-summary", dependencies=[Depends(require_authenticated)])
async def amenities_summary(
    cid: UUID = Depends(get_current_condominium_id),
    svc: ChatbotService = Depends(_service),
):
    return success(await svc.amenities_summary(cid))


@router.get("/finance-summary", dependencies=[Depends(require_authenticated)])
async def finance_summary(
    cid: UUID = Depends(get_current_condominium_id),
    property_id: UUID | None = None,
    svc: ChatbotService = Depends(_service),
):
    return success(await svc.finance_summary(cid, property_id))


@router.get("/latest-news", dependencies=[Depends(require_authenticated)])
async def latest_news(
    cid: UUID = Depends(get_current_condominium_id),
    limit: int = Query(5, ge=1, le=10),
    svc: ChatbotService = Depends(_service),
):
    return success(await svc.latest_news_summary(cid, limit))


@router.get("/parking-summary", dependencies=[Depends(require_authenticated)])
async def parking_summary(
    cid: UUID = Depends(get_current_condominium_id),
    svc: ChatbotService = Depends(_service),
):
    return success(await svc.parking_summary(cid))


@router.get("/pets-summary", dependencies=[Depends(require_authenticated)])
async def pets_summary(
    cid: UUID = Depends(get_current_condominium_id),
    svc: ChatbotService = Depends(_service),
):
    return success(await svc.pets_summary(cid))


@router.get("/short-rent-properties", dependencies=[Depends(require_authenticated)])
async def short_rent_properties(
    cid: UUID = Depends(get_current_condominium_id),
    svc: ChatbotService = Depends(_service),
):
    return success(await svc.short_rent_properties(cid))
