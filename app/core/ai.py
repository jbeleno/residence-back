"""Gemini AI service – embeddings and chat generation."""

from __future__ import annotations

import logging

from google import genai
from google.genai import errors as genai_errors

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


async def get_embedding(text: str) -> list[float]:
    """Generate a 768-dim embedding vector via Gemini embedding model."""
    client = _get_client()
    response = client.models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=text,
        config={"output_dimensionality": 768},
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

    try:
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
    except genai_errors.ClientError as exc:
        if exc.code == 429:
            logger.warning("Gemini rate-limit reached: %s", exc)
            return (
                "En este momento el servicio de IA está saturado. "
                "Por favor intenta de nuevo en unos segundos."
            )
        raise
