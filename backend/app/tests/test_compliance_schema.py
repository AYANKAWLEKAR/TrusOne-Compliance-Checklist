import pytest

from app.schemas.common import SourceCitation
from app.schemas.compliance import (
    ComplianceReportResponse,
    ComplianceReportSummary,
    TaskDetail,
    TaskItem,
)


def build_task(**overrides) -> TaskItem:
    payload = {
        "id": "maintain-sops",
        "title": "Maintain SOPs",
        "source": "OSHA",
        "source_url": "https://example.com/sops",
        "priority_label": "High Priority",
        "meta_label": "Required by 29 CFR 1910.119",
        "default_completed": False,
        "citations": ["doc:1"],
        "detail": TaskDetail(
            explanation="Keep SOPs current.",
            next_step="Review the current SOPs.",
            why_it_matters="Inspectors expect to see them.",
            notes="Store the approved version with revision history.",
        ),
    }
    payload.update(overrides)
    return TaskItem(**payload)


def test_compliance_response_requires_known_citations() -> None:
    with pytest.raises(ValueError):
        ComplianceReportResponse(
            summary=ComplianceReportSummary(
                analysis_text="One task mapped from OSHA.",
                total_tasks=1,
                completed_tasks=0,
                open_tasks=1,
                mapped_sources=["OSHA"],
            ),
            tasks=[build_task(citations=["missing"])],
            sources=[],
        )


def test_compliance_response_requires_matching_summary_counts() -> None:
    with pytest.raises(ValueError):
        ComplianceReportResponse(
            summary=ComplianceReportSummary(
                analysis_text="One task mapped from OSHA.",
                total_tasks=1,
                completed_tasks=1,
                open_tasks=0,
                mapped_sources=["OSHA"],
            ),
            tasks=[build_task(default_completed=False)],
            sources=[
                SourceCitation(
                    source_id="doc:1",
                    source_type="vector_document",
                    title="Doc",
                )
            ],
        )


def test_compliance_response_accepts_valid_task_payload() -> None:
    response = ComplianceReportResponse(
        summary=ComplianceReportSummary(
            analysis_text="Two tasks mapped from OSHA and EPA.",
            total_tasks=2,
            completed_tasks=1,
            open_tasks=1,
            mapped_sources=["OSHA", "EPA"],
        ),
        tasks=[
            build_task(default_completed=True),
            build_task(
                id="implement-training-management",
                title="Implement Training Management",
                source="EPA",
                source_url="https://example.com/training",
                priority_label="Standard",
                meta_label="Ongoing workflow",
                citations=["doc:2"],
            ),
        ],
        sources=[
            SourceCitation(
                source_id="doc:1",
                source_type="vector_document",
                title="Doc 1",
            ),
            SourceCitation(
                source_id="doc:2",
                source_type="vector_document",
                title="Doc 2",
            ),
        ],
    )

    assert response.tasks[0].id == "maintain-sops"
    assert response.summary.open_tasks == 1
