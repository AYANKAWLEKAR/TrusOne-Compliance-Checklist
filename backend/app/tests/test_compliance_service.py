import pytest

from app.schemas.compliance import ComplianceReportRequest, TaskDetail, TaskItem
from app.services.compliance import ComplianceReportService


def test_fallback_report_returns_task_payload() -> None:
    service = ComplianceReportService(db=None)  # type: ignore[arg-type]
    payload = ComplianceReportRequest(
        location="Oakland, CA",
        industry="chemical manufacturing",
        company_size="51-250",
    )
    vector_results = [
        {
            "regulation_id": 1,
            "regulation_name": "Maintain hazardous materials inventory records",
            "regulation_code_reference": "CA HMBP 6.95",
            "level": "City",
            "state": "California",
            "county": "Alameda County",
            "city_jurisdiction": "Oakland",
            "description": "Facilities must maintain current hazardous materials inventory records.",
            "action_required": "Review the current inventory log and assign an owner.",
            "search_text": "hazardous materials inventory records oakland california storage",
        }
    ]
    sources = service._build_sources(vector_results, payload)

    response = service._build_fallback_report(vector_results, payload, sources)

    assert response.summary.total_tasks == len(response.tasks)
    assert response.summary.mapped_sources == ["Oakland, California"]
    assert response.tasks[0].citations == ["reg:1"]
    assert len(response.tasks[0].detail.explanation) > 160
    assert len(response.tasks[0].detail.next_step) > 160
    assert len(response.tasks[0].detail.why_it_matters) > 160
    assert len(response.tasks[0].detail.notes) > 160
    assert response.tasks[0].title == "Maintain hazardous materials inventory records"


def test_fallback_report_uses_gap_task_when_no_sources() -> None:
    service = ComplianceReportService(db=None)  # type: ignore[arg-type]
    payload = ComplianceReportRequest(
        location="Austin, TX",
        industry="software",
        company_size="11-50",
    )
    sources = service._build_sources([], payload)

    response = service._build_fallback_report([], payload, sources)

    assert response.summary.total_tasks == 1
    assert response.tasks[0].id == "review-source-coverage"
    assert response.tasks[0].citations == ["generated:no-results"]


def test_build_filters_prefers_explicit_city_context() -> None:
    service = ComplianceReportService(db=None)  # type: ignore[arg-type]
    payload = ComplianceReportRequest(
        location="Berkeley, California",
        location_city="Berkeley",
        location_county="Alameda County",
        location_state="California",
        industry="Chemical",
        company_size="51-250",
    )

    filters = service._build_filters(payload)

    assert filters["state"] == "California"
    assert filters["county"] == "Alameda County"
    assert filters["city_jurisdiction"] == "Berkeley"


def test_normalize_llm_task_detail_expands_short_sections() -> None:
    service = ComplianceReportService(db=None)  # type: ignore[arg-type]
    payload = ComplianceReportRequest(
        location="Berkeley, California",
        location_city="Berkeley",
        location_county="Alameda County",
        location_state="California",
        industry="Chemical",
        company_size="51-250",
    )
    vector_results = [
        {
            "regulation_id": 33,
            "regulation_name": "File HMBP with Berkeley TMD",
            "regulation_code_reference": "BMC 11.52",
            "level": "City",
            "state": "California",
            "county": "Alameda County",
            "city_jurisdiction": "Berkeley",
            "description": "Businesses must file a Hazardous Materials Business Plan with Berkeley TMD.",
            "action_required": "Prepare and submit the HMBP through the CERS system.",
            "search_text": "berkeley hmbp filing",
        }
    ]
    task = TaskItem(
        id="file-hmbp",
        title="File HMBP with Berkeley TMD",
        source="Berkeley, California",
        priority_label="High Priority",
        meta_label="Required by BMC 11.52",
        default_completed=False,
        citations=["reg:33"],
        detail=TaskDetail(
            explanation="Businesses must file an HMBP.",
            next_step="Submit it through CERS.",
            why_it_matters="The city expects it.",
            notes="Use Berkeley TMD.",
        ),
    )

    normalized = service._normalize_llm_task_detail(task, payload, vector_results)

    assert len(normalized.detail.explanation) > len(task.detail.explanation)
    assert len(normalized.detail.next_step) > len(task.detail.next_step)
    assert len(normalized.detail.why_it_matters) > len(task.detail.why_it_matters)
    assert len(normalized.detail.notes) > len(task.detail.notes)


@pytest.mark.integration
def test_list_options_returns_city_level_entries(db_session) -> None:
    service = ComplianceReportService(db=db_session)

    response = service.list_options()

    assert "Chemical" in response.industries
    assert any(option.city == "Berkeley" for option in response.locations)
