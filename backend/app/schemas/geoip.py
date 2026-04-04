from pydantic import BaseModel


class GeoIPResponse(BaseModel):
    city: str | None = None
    region: str | None = None
    postal: str | None = None
    country_name: str | None = None
    formatted_location: str
