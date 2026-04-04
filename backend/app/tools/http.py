from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings


class HTTPToolClient:
    def __init__(self) -> None:
        self.timeout = settings.api_timeout_seconds

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def get(self, url: str, params: dict | None = None, headers: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
