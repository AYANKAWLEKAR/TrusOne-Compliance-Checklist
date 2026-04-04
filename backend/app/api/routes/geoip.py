from fastapi import APIRouter

from app.schemas.geoip import GeoIPResponse
from app.services.geoip import GeoIPService

router = APIRouter(prefix="/api/geoip", tags=["geoip"])


@router.post("/resolve", response_model=GeoIPResponse)
async def resolve_geoip() -> GeoIPResponse:
    return await GeoIPService().resolve()
