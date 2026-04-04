import pytest
from httpx import HTTPStatusError, Request, Response

from app.tools.http import HTTPToolClient


@pytest.mark.asyncio
async def test_http_client_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    client = HTTPToolClient()
    attempts = {"count": 0}

    async def fake_get(_self, url: str, params=None, headers=None):
        attempts["count"] += 1
        if attempts["count"] < 3:
            request = Request("GET", url)
            response = Response(500, request=request)
            raise HTTPStatusError("boom", request=request, response=response)
        request = Request("GET", url)
        return Response(200, request=request, json={"ok": True})

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get)

    response = await client.get("https://example.com")
    assert response == {"ok": True}
    assert attempts["count"] == 3
