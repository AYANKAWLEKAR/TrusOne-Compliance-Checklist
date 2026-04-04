import pytest

from app.schemas.common import SourceCitation
from app.schemas.compliance import ComplianceReportResponse, ComplianceRequirement, RegulatoryDependency, RequiredDocument, RequiredWorkflow


def test_compliance_response_requires_known_citations() -> None:
    with pytest.raises(ValueError):
        ComplianceReportResponse(
            compliance_certification_requirements=[
                ComplianceRequirement(
                    regulation_id="40 CFR 68",
                    certification_clause="Clause",
                    business_activity="Activity",
                    citations=["missing"],
                )
            ],
            regulatory_dependencies=[],
            required_documents=[],
            required_workflows=[],
            sources=[],
        )


def test_compliance_response_accepts_valid_citations() -> None:
    response = ComplianceReportResponse(
        compliance_certification_requirements=[
            ComplianceRequirement(
                regulation_id="40 CFR 68",
                certification_clause="Clause",
                business_activity="Activity",
                citations=["doc:1"],
            )
        ],
        regulatory_dependencies=[
            RegulatoryDependency(
                primary_agency="EPA",
                related_agency="OSHA",
                relationship="Overlap",
                citations=["doc:1"],
            )
        ],
        required_documents=[
            RequiredDocument(
                document_type="SOPs",
                description="desc",
                required_by="40 CFR 68",
                citations=["doc:1"],
            )
        ],
        required_workflows=[
            RequiredWorkflow(
                workflow_name="training management",
                description="desc",
                frequency="annual",
                responsible_party="Compliance lead",
                citations=["doc:1"],
            )
        ],
        sources=[
            SourceCitation(
                source_id="doc:1",
                source_type="vector_document",
                title="Doc",
            )
        ],
    )

    assert response.sources[0].source_id == "doc:1"
