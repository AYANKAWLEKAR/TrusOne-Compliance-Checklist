from datetime import date

from pydantic import BaseModel, Field


class SeedDocument(BaseModel):
    title: str
    source_url: str
    agency: str
    regulation_id: str
    jurisdiction: str
    state: str | None = None
    county: str | None = None
    industry_sectors: list[str]
    min_employee_size: int | None = None
    max_employee_size: int | None = None
    effective_date: date | None = None
    full_text: str = Field(..., min_length=1)
    extra_metadata: dict = Field(default_factory=dict)
    required_document_types: list[str] = Field(default_factory=list)
    required_workflows: list[str] = Field(default_factory=list)


class DocumentIngestRequest(BaseModel):
    documents: list[SeedDocument]


class IngestResponse(BaseModel):
    inserted_documents: int
