from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    source_id: str = Field(..., description="Normalized citation identifier")
    source_type: str
    title: str
    url: str | None = None
    excerpt: str | None = None


class CitationBearingModel(BaseModel):
    citations: list[str] = Field(default_factory=list, min_length=1)
