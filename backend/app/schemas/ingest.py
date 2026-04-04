from datetime import date

from pydantic import BaseModel, Field


class RegulationSeedRow(BaseModel):
    industry: str
    function: str
    state: str
    county: str
    city_jurisdiction: str
    level: str
    regulation_name: str
    regulation_code_reference: str
    description: str
    action_required: str
    external_metadata: dict = Field(default_factory=dict)


class WorkbookIngestRequest(BaseModel):
    workbook_path: str = Field(..., min_length=1)


class WorkbookIngestResponse(BaseModel):
    parsed_regulations: int
    inserted_regulations: int
    updated_regulations: int
    inserted_vectors: int


class SourceDocumentIngestRequest(BaseModel):
    title: str
    source_url: str | None = None
    source_type: str
    publisher_agency: str | None = None
    publication_date: date | None = None
    effective_date: date | None = None
    checksum: str | None = None
    external_identifier: str | None = None
    mime_type: str | None = None
    raw_text: str | None = None
    storage_reference: str | None = None
    ingestion_status: str = "pending"
    external_metadata: dict = Field(default_factory=dict)


class SourceDocumentIngestResponse(BaseModel):
    inserted_documents: int
