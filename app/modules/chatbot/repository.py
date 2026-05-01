"""Chatbot repository – RAG operations + summary queries."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.amenity import Amenity
from app.models.catalog import PaymentStatus
from app.models.core import Condominium, Property, UserProperty
from app.models.finance import Invoice
from app.models.news import NewsBoard
from app.models.pet import Pet
from app.models.rag import ChatMessage, ChatSession, Document, DocumentChunk
from app.models.visitor import ParkingSpace


class ChatbotRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ══════════════════════════════════════════════════════════════════════
    #  RAG – Documents
    # ══════════════════════════════════════════════════════════════════════

    async def create_document(
        self, cid: UUID, title: str, source_type: str,
        original_filename: str | None, created_by: UUID,
    ) -> Document:
        doc = Document(
            condominium_id=cid, title=title, source_type=source_type,
            original_filename=original_filename, created_by=created_by,
        )
        self._db.add(doc)
        await self._db.flush()
        return doc

    async def create_chunk(
        self, document_id: int, chunk_index: int, content: str, embedding: list[float],
    ) -> None:
        emb_str = "[" + ",".join(str(v) for v in embedding) + "]"
        await self._db.execute(
            text(
                "INSERT INTO document_chunks (document_id, chunk_index, content, embedding) "
                "VALUES (:doc_id, :idx, :content, CAST(:emb AS vector))"
            ),
            {"doc_id": document_id, "idx": chunk_index, "content": content, "emb": emb_str},
        )

    async def list_documents(self, cid: UUID) -> list[Document]:
        result = await self._db.execute(
            select(Document).where(Document.condominium_id == cid).order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_document(self, doc_id: int, cid: UUID) -> Document | None:
        result = await self._db.execute(
            select(Document).where(Document.id == doc_id, Document.condominium_id == cid)
        )
        return result.scalars().first()

    async def delete_document(self, doc_id: int, cid: UUID) -> bool:
        result = await self._db.execute(
            delete(Document).where(Document.id == doc_id, Document.condominium_id == cid)
        )
        return result.rowcount > 0

    async def search_similar_chunks(self, cid: UUID, embedding: list[float], limit: int = 5) -> list[dict]:
        emb_str = "[" + ",".join(str(v) for v in embedding) + "]"
        result = await self._db.execute(
            text(
                "SELECT dc.content, dc.chunk_index, d.title, "
                "1 - (dc.embedding <=> CAST(:emb AS vector)) AS similarity "
                "FROM document_chunks dc "
                "JOIN documents d ON dc.document_id = d.id "
                "WHERE d.condominium_id = :cid "
                "ORDER BY dc.embedding <=> CAST(:emb AS vector) "
                "LIMIT :lim"
            ),
            {"cid": str(cid), "emb": emb_str, "lim": limit},
        )
        return [
            {"content": r[0], "chunk_index": r[1], "document_title": r[2], "similarity": float(r[3])}
            for r in result.fetchall()
        ]

    # ══════════════════════════════════════════════════════════════════════
    #  RAG – Chat sessions
    # ══════════════════════════════════════════════════════════════════════

    async def create_session(self, user_id: UUID, cid: UUID, title: str = "Nueva conversación") -> ChatSession:
        session = ChatSession(user_id=user_id, condominium_id=cid, title=title)
        self._db.add(session)
        await self._db.flush()
        return session

    async def get_session(self, session_id: int, user_id: UUID) -> ChatSession | None:
        result = await self._db.execute(
            select(ChatSession).options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        return result.scalars().first()

    async def list_sessions(self, user_id: UUID, cid: UUID) -> list[ChatSession]:
        result = await self._db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id, ChatSession.condominium_id == cid)
            .order_by(ChatSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_session(self, session_id: int, user_id: UUID) -> bool:
        result = await self._db.execute(
            delete(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        return result.rowcount > 0

    async def add_message(self, session_id: int, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(session_id=session_id, role=role, content=content)
        self._db.add(msg)
        await self._db.flush()
        return msg

    # ══════════════════════════════════════════════════════════════════════
    #  Legacy summary queries
    # ══════════════════════════════════════════════════════════════════════

    async def get_condominium(self, cid: UUID) -> Condominium | None:
        result = await self._db.execute(select(Condominium).where(Condominium.id == cid))
        return result.scalars().first()

    async def count_properties(self, cid: UUID) -> int:
        result = await self._db.execute(
            select(func.count(Property.id)).where(Property.condominium_id == cid, Property.deleted_at.is_(None))
        )
        return result.scalar_one()

    async def count_residents(self, cid: UUID) -> int:
        result = await self._db.execute(
            select(func.count(UserProperty.id))
            .join(Property, UserProperty.property_id == Property.id)
            .where(Property.condominium_id == cid, UserProperty.is_active.is_(True))
        )
        return result.scalar_one()

    async def count_amenities(self, cid: UUID) -> int:
        result = await self._db.execute(
            select(func.count(Amenity.id)).where(Amenity.condominium_id == cid, Amenity.is_active.is_(True))
        )
        return result.scalar_one()

    async def list_amenities(self, cid: UUID) -> list[Amenity]:
        result = await self._db.execute(
            select(Amenity).where(Amenity.condominium_id == cid, Amenity.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def list_invoices(self, cid: UUID, *, property_id: UUID | None = None) -> list[Invoice]:
        stmt = select(Invoice).where(Invoice.condominium_id == cid)
        if property_id:
            stmt = stmt.where(Invoice.property_id == property_id)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_overdue_status(self) -> PaymentStatus | None:
        result = await self._db.execute(select(PaymentStatus).where(PaymentStatus.code == "vencido"))
        return result.scalars().first()

    async def latest_news(self, cid: UUID, limit: int = 5) -> list[NewsBoard]:
        now = datetime.utcnow()
        result = await self._db.execute(
            select(NewsBoard).where(
                NewsBoard.condominium_id == cid, NewsBoard.is_published.is_(True),
                (NewsBoard.expires_at.is_(None)) | (NewsBoard.expires_at > now),
            ).order_by(NewsBoard.is_pinned.desc(), NewsBoard.publish_date.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def list_parking_spaces(self, cid: UUID) -> list[ParkingSpace]:
        result = await self._db.execute(
            select(ParkingSpace).options(selectinload(ParkingSpace.parking_type))
            .where(ParkingSpace.condominium_id == cid, ParkingSpace.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def list_pets(self, cid: UUID) -> list[Pet]:
        result = await self._db.execute(
            select(Pet).join(Property, Pet.property_id == Property.id)
            .options(selectinload(Pet.pet_species))
            .where(Property.condominium_id == cid, Pet.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def list_short_rent_properties(self, cid: UUID) -> list[Property]:
        result = await self._db.execute(
            select(Property).options(selectinload(Property.property_type))
            .where(Property.condominium_id == cid, Property.is_short_rent.is_(True), Property.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def save(self) -> None:
        await self._db.commit()

    def savepoint(self):
        """Return a SAVEPOINT context manager scoped to the current session.

        Used to isolate failures: if a per-chunk insert raises, only the
        savepoint is rolled back and the outer transaction stays usable.
        """
        return self._db.begin_nested()
