"""One-time migration: create RAG tables in Neon."""
import asyncio
from app.core.database import engine
from sqlalchemy import text


async def create_tables():
    async with engine.begin() as conn:
        await conn.execute(text(
            "CREATE TABLE IF NOT EXISTS documents ("
            "id SERIAL PRIMARY KEY, "
            "condominium_id UUID NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE, "
            "title VARCHAR(255) NOT NULL, "
            "source_type VARCHAR(30) NOT NULL DEFAULT 'text', "
            "original_filename VARCHAR(500), "
            "created_by UUID REFERENCES users(id), "
            "created_at TIMESTAMPTZ DEFAULT NOW())"
        ))
        await conn.execute(text(
            "CREATE TABLE IF NOT EXISTS document_chunks ("
            "id SERIAL PRIMARY KEY, "
            "document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE, "
            "chunk_index INTEGER NOT NULL DEFAULT 0, "
            "content TEXT NOT NULL, "
            "embedding vector(768), "
            "created_at TIMESTAMPTZ DEFAULT NOW())"
        ))
        await conn.execute(text(
            "CREATE TABLE IF NOT EXISTS chat_sessions ("
            "id SERIAL PRIMARY KEY, "
            "user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, "
            "condominium_id UUID NOT NULL REFERENCES condominiums(id) ON DELETE CASCADE, "
            "title VARCHAR(255) DEFAULT 'Nueva conversacion', "
            "created_at TIMESTAMPTZ DEFAULT NOW())"
        ))
        await conn.execute(text(
            "CREATE TABLE IF NOT EXISTS chat_messages ("
            "id SERIAL PRIMARY KEY, "
            "session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE, "
            "role VARCHAR(20) NOT NULL, "
            "content TEXT NOT NULL, "
            "created_at TIMESTAMPTZ DEFAULT NOW())"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_documents_condo ON documents(condominium_id)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id, condominium_id)"
        ))
    print("All RAG tables created OK")


asyncio.run(create_tables())
