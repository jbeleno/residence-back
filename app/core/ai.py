"""Gemini AI service – embeddings and chat generation."""

from __future__ import annotations

from google import genai

from app.core.config import settings

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


async def get_embedding(text: str) -> list[float]:
    """Generate a 768-dim embedding vector via Gemini text-embedding-004."""
    client = _get_client()
    response = client.models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=text,
    )
    return list(response.embeddings[0].values)


async def chat_completion(
    system_prompt: str,
    messages: list[dict[str, str]],
    user_message: str,
) -> str:
    """Generate a chat response via Gemini flash-lite."""
    client = _get_client()

    # Build contents for Gemini
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    response = client.models.generate_content(
        model=settings.GEMINI_CHAT_MODEL,
        contents=contents,
        config={
            "system_instruction": system_prompt,
            "temperature": 0.3,
            "max_output_tokens": 1024,
        },
    )
    return response.text or "No pude generar una respuesta."
