"""Tests for chatbot module: service logic (RAG, documents, sessions, summaries)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.chatbot.service import ChatbotService, _chunk_text


# ── Chunk text utility ────────────────────────────────────────────────────


class TestChunkText:
    def test_short_text(self):
        chunks = _chunk_text("Hello world")
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"

    def test_empty_text(self):
        chunks = _chunk_text("")
        assert chunks == []

    def test_whitespace_text(self):
        chunks = _chunk_text("   ")
        assert chunks == []

    def test_long_text_splits(self):
        text = "A" * 2000
        chunks = _chunk_text(text)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c) <= 800

    def test_overlap(self):
        text = "X" * 1600
        chunks = _chunk_text(text)
        # With 800 char chunks and 100 overlap, second chunk starts at 700
        assert len(chunks) >= 2


# ── Mock helpers ──────────────────────────────────────────────────────────


def _mock_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.save = AsyncMock()
    return repo


def _mock_document(doc_id=1, title="Reglamento"):
    doc = MagicMock()
    doc.id = doc_id
    doc.title = title
    doc.source_type = "text"
    doc.original_filename = None
    doc.created_at = MagicMock(isoformat=MagicMock(return_value="2026-01-01T00:00:00"))
    return doc


def _mock_session(sid=1, title="Chat", messages=None):
    session = MagicMock()
    session.id = sid
    session.title = title
    session.messages = messages or []
    session.created_at = MagicMock(isoformat=MagicMock(return_value="2026-01-01T00:00:00"))
    return session


def _mock_message(role="user", content="Hola"):
    msg = MagicMock()
    msg.role = role
    msg.content = content
    msg.created_at = MagicMock(isoformat=MagicMock(return_value="2026-01-01T00:00:00"))
    return msg


def _mock_condo(name="Condo Test"):
    c = MagicMock()
    c.name = name
    c.address = "Calle 1"
    c.city = "Bogotá"
    c.phone = "123"
    c.email = "c@c.com"
    c.timezone = "America/Bogota"
    c.currency = "COP"
    c.visitor_parking_hourly_rate = 5000
    return c


# ══════════════════════════════════════════════════════════════════════════
#  Document management
# ══════════════════════════════════════════════════════════════════════════


class TestDocumentUpload:
    @patch("app.modules.chatbot.service.get_embedding", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_upload_success(self, mock_embed):
        mock_embed.return_value = [0.1] * 768
        doc = _mock_document()

        repo = _mock_repo()
        repo.create_document = AsyncMock(return_value=doc)
        repo.create_chunk = AsyncMock()

        svc = ChatbotService(repo)
        cid, uid = uuid.uuid4(), uuid.uuid4()
        result = await svc.upload_document(cid, uid, "Test Doc", "Some content here")

        assert result["document_id"] == 1
        assert result["chunks_created"] >= 1
        repo.create_document.assert_called_once()
        repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_empty_content(self):
        repo = _mock_repo()
        svc = ChatbotService(repo)

        with pytest.raises(BadRequestError, match="vacío"):
            await svc.upload_document(uuid.uuid4(), uuid.uuid4(), "T", "   ")


class TestDocumentList:
    @pytest.mark.asyncio
    async def test_list_documents(self):
        d1 = _mock_document(1, "Doc A")
        d2 = _mock_document(2, "Doc B")

        repo = _mock_repo()
        repo.list_documents = AsyncMock(return_value=[d1, d2])

        svc = ChatbotService(repo)
        result = await svc.list_documents(uuid.uuid4())

        assert len(result) == 2
        assert result[0]["title"] == "Doc A"


class TestDocumentDelete:
    @pytest.mark.asyncio
    async def test_delete_success(self):
        repo = _mock_repo()
        repo.delete_document = AsyncMock(return_value=True)

        svc = ChatbotService(repo)
        result = await svc.delete_document(1, uuid.uuid4())

        assert "eliminado" in result["message"]

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        repo = _mock_repo()
        repo.delete_document = AsyncMock(return_value=False)

        svc = ChatbotService(repo)
        with pytest.raises(NotFoundError):
            await svc.delete_document(999, uuid.uuid4())


# ══════════════════════════════════════════════════════════════════════════
#  RAG Chat
# ══════════════════════════════════════════════════════════════════════════


class TestChat:
    @patch("app.modules.chatbot.service.chat_completion", new_callable=AsyncMock)
    @patch("app.modules.chatbot.service.get_embedding", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_new_session(self, mock_embed, mock_chat):
        mock_embed.return_value = [0.1] * 768
        mock_chat.return_value = "Hola, soy Resi."

        session = _mock_session()
        repo = _mock_repo()
        repo.create_session = AsyncMock(return_value=session)
        repo.search_similar_chunks = AsyncMock(return_value=[])
        repo.get_condominium = AsyncMock(return_value=_mock_condo())
        repo.count_properties = AsyncMock(return_value=10)
        repo.count_residents = AsyncMock(return_value=5)
        repo.count_amenities = AsyncMock(return_value=3)
        repo.list_amenities = AsyncMock(return_value=[])
        repo.latest_news = AsyncMock(return_value=[])
        repo.add_message = AsyncMock()

        svc = ChatbotService(repo)
        cid, uid = uuid.uuid4(), uuid.uuid4()
        result = await svc.chat(cid, uid, None, "Hola")

        assert result["session_id"] == 1
        assert result["response"] == "Hola, soy Resi."
        repo.create_session.assert_called_once()
        assert repo.add_message.call_count == 2  # user + assistant

    @patch("app.modules.chatbot.service.chat_completion", new_callable=AsyncMock)
    @patch("app.modules.chatbot.service.get_embedding", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_existing_session(self, mock_embed, mock_chat):
        mock_embed.return_value = [0.1] * 768
        mock_chat.return_value = "Respuesta."

        session = _mock_session(sid=5, messages=[_mock_message()])
        repo = _mock_repo()
        repo.get_session = AsyncMock(return_value=session)
        repo.search_similar_chunks = AsyncMock(return_value=[
            {"content": "texto", "chunk_index": 0, "document_title": "Reg", "similarity": 0.8}
        ])
        repo.get_condominium = AsyncMock(return_value=_mock_condo())
        repo.count_properties = AsyncMock(return_value=0)
        repo.count_residents = AsyncMock(return_value=0)
        repo.count_amenities = AsyncMock(return_value=0)
        repo.list_amenities = AsyncMock(return_value=[])
        repo.latest_news = AsyncMock(return_value=[])
        repo.add_message = AsyncMock()

        svc = ChatbotService(repo)
        result = await svc.chat(uuid.uuid4(), uuid.uuid4(), 5, "Pregunta")

        assert result["session_id"] == 5
        assert len(result["sources"]) == 1
        assert result["sources"][0]["document"] == "Reg"

    @pytest.mark.asyncio
    async def test_session_not_found(self):
        repo = _mock_repo()
        repo.get_session = AsyncMock(return_value=None)

        svc = ChatbotService(repo)
        with pytest.raises(NotFoundError, match="Sesión de chat"):
            await svc.chat(uuid.uuid4(), uuid.uuid4(), 999, "Hola")


# ══════════════════════════════════════════════════════════════════════════
#  Session management
# ══════════════════════════════════════════════════════════════════════════


class TestSessionManagement:
    @pytest.mark.asyncio
    async def test_list_sessions(self):
        s1 = _mock_session(1, "Chat 1")
        s2 = _mock_session(2, "Chat 2")

        repo = _mock_repo()
        repo.list_sessions = AsyncMock(return_value=[s1, s2])

        svc = ChatbotService(repo)
        result = await svc.list_sessions(uuid.uuid4(), uuid.uuid4())

        assert len(result) == 2
        assert result[0]["title"] == "Chat 1"

    @pytest.mark.asyncio
    async def test_get_session_messages(self):
        msgs = [_mock_message("user", "hola"), _mock_message("assistant", "respuesta")]
        session = _mock_session(1, "Chat", msgs)

        repo = _mock_repo()
        repo.get_session = AsyncMock(return_value=session)

        svc = ChatbotService(repo)
        result = await svc.get_session_messages(1, uuid.uuid4())

        assert result["session_id"] == 1
        assert len(result["messages"]) == 2
        assert result["messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        repo = _mock_repo()
        repo.get_session = AsyncMock(return_value=None)

        svc = ChatbotService(repo)
        with pytest.raises(NotFoundError):
            await svc.get_session_messages(999, uuid.uuid4())

    @pytest.mark.asyncio
    async def test_delete_session(self):
        repo = _mock_repo()
        repo.delete_session = AsyncMock(return_value=True)

        svc = ChatbotService(repo)
        result = await svc.delete_session(1, uuid.uuid4())
        assert "eliminada" in result["message"]

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self):
        repo = _mock_repo()
        repo.delete_session = AsyncMock(return_value=False)

        svc = ChatbotService(repo)
        with pytest.raises(NotFoundError):
            await svc.delete_session(999, uuid.uuid4())


# ══════════════════════════════════════════════════════════════════════════
#  Legacy summaries
# ══════════════════════════════════════════════════════════════════════════


class TestLegacySummaries:
    @pytest.mark.asyncio
    async def test_condominium_info(self):
        repo = _mock_repo()
        repo.get_condominium = AsyncMock(return_value=_mock_condo())
        repo.count_properties = AsyncMock(return_value=20)
        repo.count_residents = AsyncMock(return_value=15)
        repo.count_amenities = AsyncMock(return_value=5)

        svc = ChatbotService(repo)
        result = await svc.condominium_info(uuid.uuid4())

        assert result["name"] == "Condo Test"
        assert result["total_properties"] == 20
        assert result["total_residents"] == 15
        assert result["total_amenities"] == 5

    @pytest.mark.asyncio
    async def test_condominium_info_not_found(self):
        repo = _mock_repo()
        repo.get_condominium = AsyncMock(return_value=None)
        repo.count_properties = AsyncMock(return_value=0)
        repo.count_residents = AsyncMock(return_value=0)
        repo.count_amenities = AsyncMock(return_value=0)

        svc = ChatbotService(repo)
        result = await svc.condominium_info(uuid.uuid4())

        assert result["name"] is None

    @pytest.mark.asyncio
    async def test_amenities_summary(self):
        amen = MagicMock()
        amen.id = 1
        amen.name = "Piscina"
        amen.description = "Piscina principal"
        amen.capacity = 50
        amen.hourly_cost = 10000
        amen.requires_approval = False
        amen.available_from = None
        amen.available_until = None

        repo = _mock_repo()
        repo.list_amenities = AsyncMock(return_value=[amen])

        svc = ChatbotService(repo)
        result = await svc.amenities_summary(uuid.uuid4())

        assert len(result) == 1
        assert result[0]["name"] == "Piscina"

    @pytest.mark.asyncio
    async def test_finance_summary(self):
        inv = MagicMock()
        inv.amount = 100000
        inv.balance = 30000
        inv.payment_status_id = uuid.uuid4()

        repo = _mock_repo()
        repo.list_invoices = AsyncMock(return_value=[inv])
        repo.get_overdue_status = AsyncMock(return_value=None)

        svc = ChatbotService(repo)
        result = await svc.finance_summary(uuid.uuid4())

        assert result["total_invoices"] == 1
        assert result["total_charged"] == 100000
        assert result["total_pending"] == 30000
        assert result["overdue_count"] == 0

    @pytest.mark.asyncio
    async def test_parking_summary(self):
        space = MagicMock()
        pt = MagicMock()
        pt.name = "Cubierto"
        space.parking_type = pt

        repo = _mock_repo()
        repo.list_parking_spaces = AsyncMock(return_value=[space])

        svc = ChatbotService(repo)
        result = await svc.parking_summary(uuid.uuid4())

        assert result["total_spaces"] == 1
        assert result["by_type"]["Cubierto"] == 1

    @pytest.mark.asyncio
    async def test_pets_summary(self):
        pet = MagicMock()
        sp = MagicMock()
        sp.name = "Perro"
        pet.pet_species = sp

        repo = _mock_repo()
        repo.list_pets = AsyncMock(return_value=[pet])

        svc = ChatbotService(repo)
        result = await svc.pets_summary(uuid.uuid4())

        assert result["total_pets"] == 1
        assert result["by_species"]["Perro"] == 1

    @pytest.mark.asyncio
    async def test_short_rent_properties(self):
        prop = MagicMock()
        prop.id = uuid.uuid4()
        prop.number = "101"
        prop.block = "A"
        prop.floor = 1
        pt = MagicMock()
        pt.name = "Apartamento"
        prop.property_type = pt

        repo = _mock_repo()
        repo.list_short_rent_properties = AsyncMock(return_value=[prop])

        svc = ChatbotService(repo)
        result = await svc.short_rent_properties(uuid.uuid4())

        assert len(result) == 1
        assert result[0]["number"] == "101"
        assert result[0]["property_type"] == "Apartamento"

    @pytest.mark.asyncio
    async def test_latest_news_summary(self):
        news = MagicMock()
        news.id = 1
        news.title = "Mantenimiento"
        news.content = "Corte de agua mañana."
        news.is_pinned = True
        news.publish_date = MagicMock(isoformat=MagicMock(return_value="2026-01-01"))

        repo = _mock_repo()
        repo.latest_news = AsyncMock(return_value=[news])

        svc = ChatbotService(repo)
        result = await svc.latest_news_summary(uuid.uuid4())

        assert len(result) == 1
        assert result[0]["title"] == "Mantenimiento"
        assert result[0]["is_pinned"] is True
