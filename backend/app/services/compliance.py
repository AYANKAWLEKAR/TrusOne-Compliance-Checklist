from __future__ import annotations

import json
import re

from openai import AsyncOpenAI
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.ingestion.embeddings import EmbeddingService
from app.schemas.common import SourceCitation
from app.schemas.compliance import (
    ComplianceLocationOption,
    ComplianceOptionsResponse,
    ComplianceReportRequest,
    ComplianceReportResponse,
    ComplianceReportSummary,
    ComplianceTaskSynthesis,
    TaskDetail,
    TaskItem,
)
from app.db.models import Regulation
from app.tools.vector_search import VectorSearchTool


class ComplianceReportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding_service = EmbeddingService()
        self.vector_search = VectorSearchTool(db)
        self.client = (
            AsyncOpenAI(api_key=settings.openai_api_key)
            if settings.openai_api_key
            else None
        )

    async def generate_report(
        self,
        payload: ComplianceReportRequest,
    ) -> ComplianceReportResponse:
        query = (
            f"Compliance requirements for {payload.industry} companies in {payload.location} "
            f"with company size {payload.company_size}"
        )
        if payload.compliance_status:
            query += f". Current compliance status: {payload.compliance_status}"

        query_embedding = await self.embedding_service.embed(query)
        filters = self._build_filters(payload)
        vector_results = self.vector_search.search(query_embedding, filters=filters, top_k=5)
        sources = self._build_sources(vector_results, payload)

        if self.client is not None and vector_results:
            report = await self._generate_with_llm(payload, vector_results, sources)
            if report is not None:
                return report

        return self._build_fallback_report(vector_results, payload, sources)

    def list_options(self) -> ComplianceOptionsResponse:
        industries = self.db.execute(
            select(Regulation.industry)
            .where(Regulation.function.ilike("Storage"))
            .distinct()
            .order_by(Regulation.industry.asc())
        ).scalars().all()

        location_rows = self.db.execute(
            select(
                Regulation.city_jurisdiction,
                Regulation.county,
                Regulation.state,
            )
            .where(
                Regulation.function.ilike("Storage"),
                Regulation.city_jurisdiction != "All",
            )
            .distinct()
            .order_by(
                Regulation.state.asc(),
                Regulation.county.asc(),
                Regulation.city_jurisdiction.asc(),
            )
        ).all()

        locations = [
            ComplianceLocationOption(
                value=_format_location_label(city, county, state),
                display_label=_format_location_label(city, county, state),
                city=city,
                county=county,
                state=state,
                aliases=_location_aliases(city, county, state),
            )
            for city, county, state in location_rows
        ]

        return ComplianceOptionsResponse(industries=industries, locations=locations)

    def _build_filters(self, payload: ComplianceReportRequest) -> dict:
        filters = {
            "industry": payload.industry,
            "function": "Storage",
        }

        if payload.location_state:
            filters["state"] = payload.location_state
        if payload.location_county:
            filters["county"] = payload.location_county
        if payload.location_city:
            filters["city_jurisdiction"] = payload.location_city
        elif payload.location:
            normalized_location = payload.location.lower()
            city = _extract_city(payload.location)

            if "ca" in normalized_location or "california" in normalized_location:
                filters["state"] = "California"
            if "alameda" in normalized_location or city in {"oakland", "berkeley"}:
                filters["county"] = "Alameda County"
            if city == "berkeley":
                filters["city_jurisdiction"] = "Berkeley"
            elif city == "unincorporatedareas":
                filters["city_jurisdiction"] = "Unincorporated Areas"

        return filters

    async def _generate_with_llm(
        self,
        payload: ComplianceReportRequest,
        vector_results: list[dict],
        sources: list[SourceCitation],
    ) -> ComplianceReportResponse | None:
        source_context = []
        for item in vector_results:
            source_context.append(
                {
                    "source_id": f"reg:{item['regulation_id']}",
                    "regulation_name": item["regulation_name"],
                    "regulation_code_reference": item["regulation_code_reference"],
                    "level": item["level"],
                    "state": item["state"],
                    "county": item["county"],
                    "city_jurisdiction": item["city_jurisdiction"],
                    "description": item["description"],
                    "action_required": item["action_required"],
                    "search_text_excerpt": item["search_text"][:320],
                }
            )

        prompt = (
            "Return JSON only. Synthesize the retrieved regulatory sources into a "
            "wireframe-first checklist payload with exactly two top-level keys: "
            "summary and tasks.\n"
            "summary must contain analysis_text, total_tasks, completed_tasks, "
            "open_tasks, mapped_sources.\n"
            "tasks must be an array of action-oriented checklist tasks. Every "
            "task must contain: id, title, source, source_url, priority_label, "
            "meta_label, default_completed, citations, detail.\n"
            "detail must contain: explanation, next_step, why_it_matters, notes.\n"
            "Requirements:\n"
            "- Each detail field must be a single paragraph of 2 to 4 full sentences.\n"
            "- Do not use bullets, fragments, or overly terse wording inside detail fields.\n"
            "- Use only citation ids from the provided sources.\n"
            "- ids must be stable, lowercase, slug-like strings.\n"
            "- default_completed should be false unless the source clearly "
            "implies a demonstrably completed baseline.\n"
            "- Do not output section lists, markdown, or commentary outside the "
            "JSON object.\n"
            "- Make tasks concrete enough to render directly into a task list "
            "and detail modal."
        )

        response = await self.client.responses.create(
            model=settings.openai_chat_model,
            input=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        f"Company profile:\n"
                        f"- Location: {payload.location}\n"
                        f"- Industry: {payload.industry}\n"
                        f"- Company size: {payload.company_size}\n"
                        f"- Current compliance status: {payload.compliance_status or 'Not provided'}\n\n"
                        f"Retrieved sources:\n{json.dumps(source_context, ensure_ascii=False)}"
                    ),
                },
            ],
        )
        if not response.output_text:
            return None

        try:
            synthesis = ComplianceTaskSynthesis.model_validate_json(response.output_text)
            normalized_tasks = [
                self._normalize_llm_task_detail(task, payload, vector_results)
                for task in synthesis.tasks
            ]
            return ComplianceReportResponse(
                summary=synthesis.summary,
                tasks=normalized_tasks,
                sources=sources,
            )
        except ValidationError:
            return None

    def _build_sources(
        self,
        vector_results: list[dict],
        payload: ComplianceReportRequest,
    ) -> list[SourceCitation]:
        sources = [
            SourceCitation(
                source_id=f"reg:{item['regulation_id']}",
                source_type="regulation_vector",
                title=item["regulation_name"],
                excerpt=item["description"][:240],
            )
            for item in vector_results
        ]

        if sources:
            return sources

        return [
            SourceCitation(
                source_id="generated:no-results",
                source_type="system_notice",
                title="No matching regulatory seeds found",
                excerpt=(
                    f"No local seeded regulations matched {payload.industry} in "
                    f"{payload.location}."
                ),
            )
        ]

    def _build_fallback_report(
        self,
        vector_results: list[dict],
        payload: ComplianceReportRequest,
        sources: list[SourceCitation],
    ) -> ComplianceReportResponse:
        tasks = self._build_fallback_tasks(vector_results, payload)
        mapped_sources = list(dict.fromkeys(task.source for task in tasks))
        completed_tasks = sum(1 for task in tasks if task.default_completed)
        summary = ComplianceReportSummary(
            analysis_text=self._build_analysis_text(payload, tasks, mapped_sources),
            total_tasks=len(tasks),
            completed_tasks=completed_tasks,
            open_tasks=len(tasks) - completed_tasks,
            mapped_sources=mapped_sources,
        )
        return ComplianceReportResponse(summary=summary, tasks=tasks, sources=sources)

    def _build_fallback_tasks(
        self,
        vector_results: list[dict],
        payload: ComplianceReportRequest,
    ) -> list[TaskItem]:
        tasks: list[TaskItem] = []
        seen_ids: set[str] = set()

        for index, item in enumerate(vector_results):
            citation = [f"reg:{item['regulation_id']}"]
            task_id = self._slugify(item["regulation_code_reference"])

            if task_id in seen_ids:
                continue

            seen_ids.add(task_id)
            source_label = self._source_label(item)
            priority_label = "High Priority" if index == 0 else "Standard"

            tasks.append(
                TaskItem(
                    id=task_id,
                    title=item["regulation_name"],
                    source=source_label,
                    source_url=None,
                    priority_label=priority_label,
                    meta_label=f"Required by {item['regulation_code_reference']}",
                    default_completed=False,
                    citations=citation,
                    detail=TaskDetail(
                        explanation=self._build_explanation_paragraph(item, payload),
                        next_step=self._build_next_step_paragraph(item, payload),
                        why_it_matters=self._build_why_it_matters_paragraph(item, payload),
                        notes=self._build_notes_paragraph(item, payload),
                    ),
                )
            )

        if tasks:
            return tasks

        return [
            TaskItem(
                id="review-source-coverage",
                title="Review source coverage for this profile",
                source="System notice",
                source_url=None,
                priority_label="High Priority",
                meta_label="No matching seeds",
                default_completed=False,
                citations=["generated:no-results"],
                detail=TaskDetail(
                    explanation=(
                        "The current local regulation dataset does not contain a close "
                        "match for the selected company profile. That usually means "
                        "the city-level lookup, storage function, or industry label "
                        "does not line up with the workbook rows currently loaded "
                        "into this environment."
                    ),
                    next_step=(
                        "Run the checklist workbook import for the relevant jurisdiction "
                        "and function, then regenerate the report. If you expected a "
                        "match for this city, confirm the workbook contains rows for "
                        "that city and that the imported industry label matches the "
                        "selection made in the UI."
                    ),
                    why_it_matters=(
                        "The checklist is only as strong as the regulation coverage "
                        "behind it. Missing seeded data creates blind spots in the "
                        "task list, and a city-specific request can miss important "
                        "county or city obligations if the underlying workbook does "
                        "not include those rows."
                    ),
                    notes=(
                        f"No local regulations matched {payload.industry} in "
                        f"{payload.location}. Apply the latest Supabase migrations, "
                        "re-import the workbook, and confirm the request is using a "
                        "supported city label before relying on this environment."
                    ),
                ),
            )
        ]

    def _build_analysis_text(
        self,
        payload: ComplianceReportRequest,
        tasks: list[TaskItem],
        mapped_sources: list[str],
    ) -> str:
        source_text = (
            ", ".join(mapped_sources[:3]) if mapped_sources else "available sources"
        )
        return (
            f"Based on the {payload.industry} profile in {payload.location}, "
            f"the current retrieval set maps {len(tasks)} actionable compliance "
            f"tasks across {source_text}. The checklist emphasizes concrete "
            "regulatory actions that can be assigned, tracked, and evidenced."
        )

    @staticmethod
    def _jurisdiction_text(item: dict) -> str:
        if item.get("city_jurisdiction") and item["city_jurisdiction"].lower() != "all":
            return f"{item['city_jurisdiction']}, {item['state']}"
        if item.get("county") and item["county"].lower() != "all":
            return f"{item['county']}, {item['state']}"
        if item.get("state") and item["state"].lower() != "all":
            return item["state"]
        return item["level"]

    @classmethod
    def _source_label(cls, item: dict) -> str:
        return cls._jurisdiction_text(item)

    def _normalize_llm_task_detail(
        self,
        task: TaskItem,
        payload: ComplianceReportRequest,
        vector_results: list[dict],
    ) -> TaskItem:
        source_item = self._source_item_for_task(task, vector_results)

        explanation = task.detail.explanation
        next_step = task.detail.next_step
        why_it_matters = task.detail.why_it_matters
        notes = task.detail.notes

        if source_item is not None:
            explanation = self._ensure_detail_paragraph(
                explanation,
                self._build_explanation_paragraph(source_item, payload),
            )
            next_step = self._ensure_detail_paragraph(
                next_step,
                self._build_next_step_paragraph(source_item, payload),
            )
            why_it_matters = self._ensure_detail_paragraph(
                why_it_matters,
                self._build_why_it_matters_paragraph(source_item, payload),
            )
            notes = self._ensure_detail_paragraph(
                notes,
                self._build_notes_paragraph(source_item, payload),
            )
        else:
            explanation = self._ensure_detail_paragraph(
                explanation,
                (
                    f"This requirement should be interpreted in the context of "
                    f"{payload.industry} operations in {payload.location}, with a "
                    "clear owner, implementation evidence, and a documented link "
                    "between the regulation and the operating process it controls."
                ),
            )
            next_step = self._ensure_detail_paragraph(
                next_step,
                (
                    "Translate the requirement into a dated action item, assign an "
                    "owner, and define what evidence will prove completion before the "
                    "task is treated as closed."
                ),
            )
            why_it_matters = self._ensure_detail_paragraph(
                why_it_matters,
                (
                    "Short explanations tend to hide operational risk, so the task "
                    "should be backed by enough context for a reviewer to understand "
                    "why the control matters during an audit or inspection."
                ),
            )
            notes = self._ensure_detail_paragraph(
                notes,
                (
                    "Capture supporting references, retention expectations, and the "
                    "internal source of truth so the requirement can be defended "
                    "quickly during review."
                ),
            )

        return task.model_copy(
            update={
                "detail": TaskDetail(
                    explanation=explanation,
                    next_step=next_step,
                    why_it_matters=why_it_matters,
                    notes=notes,
                )
            }
        )

    @staticmethod
    def _ensure_detail_paragraph(text: str, fallback: str) -> str:
        normalized = " ".join(text.split())
        sentence_count = len(re.findall(r"[.!?]", normalized))
        if len(normalized) >= 140 and sentence_count >= 2:
            return normalized

        return _merge_paragraph_sentences(normalized, fallback)

    @staticmethod
    def _source_item_for_task(task: TaskItem, vector_results: list[dict]) -> dict | None:
        citation = next(iter(task.citations), None)
        if not citation or not citation.startswith("reg:"):
            return None

        try:
            regulation_id = int(citation.removeprefix("reg:"))
        except ValueError:
            return None

        return next(
            (item for item in vector_results if item["regulation_id"] == regulation_id),
            None,
        )

    @staticmethod
    def _build_explanation_paragraph(item: dict, payload: ComplianceReportRequest) -> str:
        return (
            f"{item['description']} In the current {payload.industry} profile for "
            f"{payload.location}, this requirement should be treated as an operating "
            "control rather than background guidance. The regulation is part of the "
            f"{item['level'].lower()} layer of the compliance stack, so it needs to be "
            "translated into a concrete internal expectation that teams can follow "
            "without having to interpret the regulation on every review."
        )

    @staticmethod
    def _build_next_step_paragraph(item: dict, payload: ComplianceReportRequest) -> str:
        return (
            f"{item['action_required']} Start by assigning a named owner, defining the "
            "evidence that proves completion, and documenting where that evidence will "
            "be stored for future review. Then compare the current site process in "
            f"{payload.location} against the requirement so any gaps can be converted "
            "into a dated action plan instead of remaining as an informal to-do."
        )

    @staticmethod
    def _build_why_it_matters_paragraph(item: dict, payload: ComplianceReportRequest) -> str:
        return (
            f"{item['regulation_code_reference']} applies to {payload.industry} work in "
            f"{payload.location}, and it can be tested during an inspection, audit, or "
            "customer diligence review. If this control is missing or weak, the issue "
            "usually cascades into multiple findings because it affects how the company "
            "stores materials, trains staff, and proves that the written program matches "
            "actual site operations."
        )

    def _build_notes_paragraph(self, item: dict, payload: ComplianceReportRequest) -> str:
        return (
            f"Jurisdiction: {self._jurisdiction_text(item)}. Keep implementation "
            "evidence, owner assignments, review dates, and any supporting retention "
            "records together so the requirement can be defended quickly during a live "
            f"review of the {payload.location} operation. If this task is fulfilled by "
            "a broader company policy, note the exact document and section that satisfy "
            "the local requirement."
        )

    @staticmethod
    def _slugify(value: str) -> str:
        return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-")


def _extract_city(location: str) -> str:
    candidate = location.split(",", maxsplit=1)[0].strip().lower()
    return re.sub(r"[^a-z]+", "", candidate.replace(" ", ""))


def _format_location_label(city: str, county: str, state: str) -> str:
    if city == "Unincorporated Areas":
        return f"{city}, {county}, {state}"
    return f"{city}, {state}"


def _location_aliases(city: str, county: str, state: str) -> list[str]:
    aliases = [city, f"{city}, {state}", county, state]
    if city == "Berkeley":
        aliases.append("Berkeley, CA")
    if city == "Unincorporated Areas":
        aliases.extend(["Unincorporated Alameda County", "Unincorporated"])
    return aliases


def _merge_paragraph_sentences(primary: str, fallback: str) -> str:
    sentence_pattern = re.compile(r"[^.!?]+[.!?]?")
    merged: list[str] = []
    seen: set[str] = set()

    for source in (primary, fallback):
        for sentence in sentence_pattern.findall(source):
            cleaned = " ".join(sentence.split()).strip()
            if not cleaned:
                continue
            key = re.sub(r"[^a-z0-9]+", "", cleaned.lower())
            if key in seen:
                continue
            seen.add(key)
            merged.append(cleaned)

    return " ".join(merged)
