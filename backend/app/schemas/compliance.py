from pydantic import BaseModel, Field, model_validator

from app.schemas.common import CitationBearingModel, SourceCitation


class ComplianceReportRequest(BaseModel):
    location: str = Field(..., min_length=1)
    industry: str = Field(..., min_length=1)
    company_size: str = Field(..., min_length=1)


class ComplianceRequirement(CitationBearingModel):
    regulation_id: str
    certification_clause: str
    business_activity: str


class RegulatoryDependency(CitationBearingModel):
    primary_agency: str
    related_agency: str
    relationship: str


class RequiredDocument(CitationBearingModel):
    document_type: str
    description: str
    required_by: str


class RequiredWorkflow(CitationBearingModel):
    workflow_name: str
    description: str
    frequency: str
    responsible_party: str


class ComplianceReportResponse(BaseModel):
    compliance_certification_requirements: list[ComplianceRequirement]
    regulatory_dependencies: list[RegulatoryDependency]
    required_documents: list[RequiredDocument]
    required_workflows: list[RequiredWorkflow]
    sources: list[SourceCitation]

    @model_validator(mode="after")
    def validate_citations_present(self) -> "ComplianceReportResponse":
        source_ids = {source.source_id for source in self.sources}
        sections = [
            *self.compliance_certification_requirements,
            *self.regulatory_dependencies,
            *self.required_documents,
            *self.required_workflows,
        ]
        for item in sections:
            if not item.citations:
                raise ValueError("Every item must include at least one citation.")
            missing = [citation for citation in item.citations if citation not in source_ids]
            if missing:
                raise ValueError(f"Unknown citations referenced: {missing}")
        return self
