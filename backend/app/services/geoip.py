from __future__ import annotations

from app.config import settings
from app.schemas.geoip import GeoIPResponse
from app.tools.http import HTTPToolClient


class GeoIPService:
    def __init__(self) -> None:
        self.client = HTTPToolClient()

    async def resolve(self) -> GeoIPResponse:
        data = await self.client.get(settings.geoip_base_url)
        formatted_location = ", ".join(
            part for part in [data.get("city"), data.get("region"), data.get("postal")] if part
        )
        return GeoIPResponse(
            city=data.get("city"),
            region=data.get("region"),
            postal=data.get("postal"),
            country_name=data.get("country_name"),
            formatted_location=formatted_location,
        )
