from __future__ import annotations

import hashlib

from openai import AsyncOpenAI

from app.config import settings


def _hash_to_unit_floats(text: str, dimensions: int = 1536) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    while len(values) < dimensions:
        for byte in digest:
            values.append((byte / 255.0) * 2 - 1)
            if len(values) == dimensions:
                break
        digest = hashlib.sha256(digest).digest()
    return values


class EmbeddingService:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def embed(self, text: str) -> list[float]:
        if self.client is None:
            return _hash_to_unit_floats(text)

        response = await self.client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text,
        )
        return response.data[0].embedding
