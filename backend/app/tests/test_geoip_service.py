import pytest

from app.services.geoip import GeoIPService


@pytest.mark.asyncio
async def test_geoip_formats_location(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(_url: str, params=None, headers=None) -> dict:
        return {
            "city": "Oakland",
            "region": "California",
            "postal": "94607",
            "country_name": "United States",
        }

    service = GeoIPService()
    monkeypatch.setattr(service.client, "get", fake_get)

    response = await service.resolve()
    assert response.formatted_location == "Oakland, California, 94607"
