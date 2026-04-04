from __future__ import annotations

from datetime import date
from urllib.parse import urlencode

from app.config import settings
from app.tools.cache import TTLCache
from app.tools.http import HTTPToolClient

cache = TTLCache(settings.ecfr_cache_ttl_seconds)


class ExternalAPITools:
    def __init__(self) -> None:
        self.client = HTTPToolClient()

    async def fetch_ecfr(self, title: int, query: str, version_date: date | None = None) -> dict:
        version = (version_date or date.today()).isoformat()
        url = f"https://www.ecfr.gov/api/versioner/v1/full/{version}/title-{title}.json"
        return await self.client.get(url, params={"query": query})

    async def fetch_echo(self, **params: str) -> dict:
        return await self.client.get("https://echo.epa.gov/rest-services/echo_rest_services.get_facility_info", params=params)

    async def fetch_envirofacts(self, **params: str) -> dict:
        query = urlencode(params)
        url = f"https://enviro.epa.gov/enviro/efservice/facility/{query}/JSON"
        return await self.client.get(url)

    async def fetch_comptox(self, chemical: str) -> dict:
        headers = {}
        if settings.epa_comptox_api_key:
            headers["x-api-key"] = settings.epa_comptox_api_key
        return await self.client.get(
            "https://api-ccte.epa.gov/chemical/search/by-name",
            params={"name": chemical},
            headers=headers,
        )

    async def fetch_california_rules(self, county: str | None = None, state: str = "CA") -> dict:
        where = "1=1"
        if county:
            where = f"county='{county}'"
        return await self.client.get(
            "https://services3.arcgis.com/example/arcgis/rest/services/Rules/FeatureServer/0/query",
            params={"where": where, "f": "geojson", "state": state},
        )
