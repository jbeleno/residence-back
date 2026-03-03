"""Chatbot service – RAG chat + document management + legacy summaries."""

from __future__ import annotations

import json
from uuid import UUID

from app.core.ai import chat_completion, get_embedding
from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.chatbot.repository import ChatbotRepository

# ── Text chunking ─────────────────────────────────────────────────────────

CHUNK_SIZE = 800  # chars
CHUNK_OVERLAP = 100


def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c.strip() for c in chunks if c.strip()]


# ── System prompt ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
Eres el asistente virtual de un condominio residencial. Tu nombre es "Resi".
Responde siempre en español, de forma amable, clara y concisa.

Tienes acceso a documentos del condominio (reglamentos, normas, manuales) y a datos en tiempo real.
Cuando el usuario pregunte algo:
1. Si hay contexto relevante de los documentos, úsalo para responder, citando el documento fuente.
2. Si hay datos estructurados (finanzas, amenidades, noticias, etc.), inclúyelos.
3. Si no tienes información suficiente, dilo honestamente.
4. Nunca inventes datos financieros, fechas o montos.

{context}
"""


class ChatbotService:
    def __init__(self, repo: ChatbotRepository) -> None:
        self._repo = repo

    # ══════════════════════════════════════════════════════════════════════
    #  Document management
    # ══════════════════════════════════════════════════════════════════════

    async def upload_document(
        self, cid: UUID, user_id: UUID, title: str, content: str,
        source_type: str = "text", filename: str | None = None,
    ) -> dict:
        if not content.strip():
            raise BadRequestError("El contenido del documento está vacío")

        doc = await self._repo.create_document(cid, title, source_type, filename, user_id)
        chunks = _chunk_text(content)

        for i, chunk in enumerate(chunks):
            embedding = await get_embedding(chunk)
            await self._repo.create_chunk(doc.id, i, chunk, embedding)

        await self._repo.save()
        return {
            "document_id": doc.id,
            "title": title,
            "chunks_created": len(chunks),
            "message": f"Documento '{title}' procesado con {len(chunks)} fragmentos.",
        }

    async def list_documents(self, cid: UUID) -> list[dict]:
        docs = await self._repo.list_documents(cid)
        return [
            {
                "id": d.id,
                "title": d.title,
                "source_type": d.source_type,
                "original_filename": d.original_filename,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ]

    async def delete_document(self, doc_id: int, cid: UUID) -> dict:
        deleted = await self._repo.delete_document(doc_id, cid)
        if not deleted:
            raise NotFoundError("Documento no encontrado")
        await self._repo.save()
        return {"message": "Documento eliminado"}

    # ══════════════════════════════════════════════════════════════════════
    #  RAG Chat
    # ══════════════════════════════════════════════════════════════════════

    async def chat(
        self, cid: UUID, user_id: UUID, session_id: int | None, message: str,
    ) -> dict:
        # Get or create session
        if session_id:
            session = await self._repo.get_session(session_id, user_id)
            if session is None:
                raise NotFoundError("Sesión de chat no encontrada")
        else:
            session = await self._repo.create_session(user_id, cid, title=message[:80])

        # Build RAG context
        context_parts = []

        # 1) Vector search on documents
        query_embedding = await get_embedding(message)
        similar_chunks = await self._repo.search_similar_chunks(cid, query_embedding, limit=5)
        if similar_chunks:
            docs_context = "\n\n".join(
                f"[Documento: {c['document_title']}]\n{c['content']}"
                for c in similar_chunks
                if c["similarity"] > 0.3
            )
            if docs_context:
                context_parts.append(f"DOCUMENTOS RELEVANTES:\n{docs_context}")

        # 2) Structured data summary (lightweight)
        structured = await self._build_structured_context(cid)
        if structured:
            context_parts.append(f"DATOS DEL CONDOMINIO:\n{structured}")

        context_str = "\n\n---\n\n".join(context_parts) if context_parts else "No hay documentos cargados aún."
        system = SYSTEM_PROMPT.format(context=context_str)

        # Build message history
        history = [
            {"role": m.role, "content": m.content}
            for m in (session.messages if session.messages else [])
        ][-10:]  # last 10 messages for context

        # Call Gemini
        ai_response = await chat_completion(system, history, message)

        # Persist messages
        await self._repo.add_message(session.id, "user", message)
        await self._repo.add_message(session.id, "assistant", ai_response)
        await self._repo.save()

        return {
            "session_id": session.id,
            "response": ai_response,
            "sources": [
                {"document": c["document_title"], "similarity": round(c["similarity"], 3)}
                for c in similar_chunks
                if c["similarity"] > 0.3
            ],
        }

    async def _build_structured_context(self, cid: UUID) -> str:
        """Build a compact text summary of condo data for the LLM context."""
        parts = []
        condo = await self._repo.get_condominium(cid)
        if condo:
            parts.append(
                f"Condominio: {condo.name}, {condo.address}, {condo.city}. "
                f"Teléfono: {condo.phone}. Email: {condo.email}."
            )

        n_props = await self._repo.count_properties(cid)
        n_res = await self._repo.count_residents(cid)
        n_amen = await self._repo.count_amenities(cid)
        parts.append(f"Propiedades: {n_props}. Residentes: {n_res}. Amenidades: {n_amen}.")

        amenities = await self._repo.list_amenities(cid)
        if amenities:
            amen_list = ", ".join(a.name for a in amenities)
            parts.append(f"Amenidades disponibles: {amen_list}.")

        news = await self._repo.latest_news(cid, limit=3)
        if news:
            news_texts = "; ".join(f"{n.title}" for n in news)
            parts.append(f"Últimas noticias: {news_texts}.")

        return " ".join(parts)

    # ══════════════════════════════════════════════════════════════════════
    #  Chat session management
    # ══════════════════════════════════════════════════════════════════════

    async def list_sessions(self, user_id: UUID, cid: UUID) -> list[dict]:
        sessions = await self._repo.list_sessions(user_id, cid)
        return [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ]

    async def get_session_messages(self, session_id: int, user_id: UUID) -> dict:
        session = await self._repo.get_session(session_id, user_id)
        if session is None:
            raise NotFoundError("Sesión no encontrada")
        return {
            "session_id": session.id,
            "title": session.title,
            "messages": [
                {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat() if m.created_at else None}
                for m in session.messages
            ],
        }

    async def delete_session(self, session_id: int, user_id: UUID) -> dict:
        deleted = await self._repo.delete_session(session_id, user_id)
        if not deleted:
            raise NotFoundError("Sesión no encontrada")
        await self._repo.save()
        return {"message": "Sesión eliminada"}

    # ══════════════════════════════════════════════════════════════════════
    #  Legacy summary endpoints
    # ══════════════════════════════════════════════════════════════════════

    async def condominium_info(self, cid: UUID):
        condo = await self._repo.get_condominium(cid)
        total_props = await self._repo.count_properties(cid)
        total_residents = await self._repo.count_residents(cid)
        total_amenities = await self._repo.count_amenities(cid)
        return {
            "name": condo.name if condo else None,
            "address": condo.address if condo else None,
            "city": condo.city if condo else None,
            "phone": condo.phone if condo else None,
            "email": condo.email if condo else None,
            "total_properties": total_props,
            "total_residents": total_residents,
            "total_amenities": total_amenities,
            "timezone": condo.timezone if condo else None,
            "currency": condo.currency if condo else None,
            "visitor_parking_rate": float(condo.visitor_parking_hourly_rate) if condo else 0,
        }

    async def amenities_summary(self, cid: UUID):
        amenities = await self._repo.list_amenities(cid)
        return [
            {
                "id": a.id, "name": a.name, "description": a.description,
                "capacity": a.capacity, "hourly_cost": float(a.hourly_cost),
                "requires_approval": a.requires_approval,
                "available_from": str(a.available_from) if a.available_from else None,
                "available_until": str(a.available_until) if a.available_until else None,
            }
            for a in amenities
        ]

    async def finance_summary(self, cid: UUID, property_id: UUID | None = None):
        invoices = await self._repo.list_invoices(cid, property_id=property_id)
        total_charged = sum(float(i.amount) for i in invoices)
        total_pending = sum(float(i.balance) for i in invoices)
        overdue_status = await self._repo.get_overdue_status()
        overdue_count = sum(1 for i in invoices if overdue_status and i.payment_status_id == overdue_status.id)
        return {
            "total_invoices": len(invoices),
            "total_charged": total_charged,
            "total_paid": total_charged - total_pending,
            "total_pending": total_pending,
            "overdue_count": overdue_count,
        }

    async def latest_news_summary(self, cid: UUID, limit: int = 5):
        news = await self._repo.latest_news(cid, limit)
        return [
            {
                "id": n.id, "title": n.title,
                "content": n.content[:200] + "..." if len(n.content) > 200 else n.content,
                "is_pinned": n.is_pinned,
                "publish_date": n.publish_date.isoformat() if n.publish_date else None,
            }
            for n in news
        ]

    async def parking_summary(self, cid: UUID):
        spaces = await self._repo.list_parking_spaces(cid)
        by_type: dict[str, int] = {}
        for s in spaces:
            t = s.parking_type.name if s.parking_type else "Otro"
            by_type[t] = by_type.get(t, 0) + 1
        return {"total_spaces": len(spaces), "by_type": by_type}

    async def pets_summary(self, cid: UUID):
        pets = await self._repo.list_pets(cid)
        by_species: dict[str, int] = {}
        for p in pets:
            sp = p.pet_species.name if p.pet_species else "Otro"
            by_species[sp] = by_species.get(sp, 0) + 1
        return {"total_pets": len(pets), "by_species": by_species}

    async def short_rent_properties(self, cid: UUID):
        props = await self._repo.list_short_rent_properties(cid)
        return [
            {
                "id": str(p.id), "number": p.number, "block": p.block,
                "floor": p.floor, "property_type": p.property_type.name if p.property_type else None,
            }
            for p in props
        ]
