from __future__ import annotations

from pydantic import ValidationError
from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.ingestion.embeddings import EmbeddingService
from app.schemas.common import SourceCitation
from app.schemas.compliance import (
    ComplianceReportRequest,
    ComplianceReportResponse,
    ComplianceRequirement,
    RegulatoryDependency,
    RequiredDocument,
    RequiredWorkflow,
)
from app.tools.external_apis import ExternalAPITools
from app.tools.vector_search import VectorSearchTool


class ComplianceReportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding_service = EmbeddingService()
        self.vector_search = VectorSearchTool(db)
        self.external_apis = ExternalAPITools()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def generate_report(self, payload: ComplianceReportRequest) -> ComplianceReportResponse:
        query = (
            f"Compliance requirements for {payload.industry} companies in {payload.location} "
            f"with company size {payload.company_size}"
        )
        query_embedding = await self.embedding_service.embed(query)
        filters = self._build_filters(payload)
        vector_results = self.vector_search.search(query_embedding, filters=filters, top_k=5)

        if self.client is not None and vector_results:
            report = await self._generate_with_llm(payload, vector_results)
            if report is not None:
                return report

        return self._build_fallback_report(vector_results, payload)

    def _build_filters(self, payload: ComplianceReportRequest) -> dict:
        filters = {"industry": payload.industry, "company_size": payload.company_size}
        if "ca" in payload.location.lower() or "california" in payload.location.lower():
            filters["state"] = "CA"
        if "alameda" in payload.location.lower():
            filters["county"] = "Alameda"
        return filters

    async def _generate_with_llm(
        self,
        payload: ComplianceReportRequest,
        vector_results: list[dict],
    ) -> ComplianceReportResponse | None:
        prompt = (
            "Produce a JSON object with compliance_certification_requirements, "
            "regulatory_dependencies, required_documents, required_workflows, and sources. "
            "Every list item must cite one or more source_ids from sources."
        )
        response = await self.client.responses.create(
            model=settings.openai_chat_model,
            input=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        f"Location: {payload.location}\n"
                        f"Industry: {payload.industry}\n"
                        f"Company size: {payload.company_size}\n"
                        f"Retrieved sources: {vector_results}"
                    ),
                },
            ],
        )
        if not response.output_text:
            return None
        try:
            return ComplianceReportResponse.model_validate_json(response.output_text)
        except ValidationError:
            return None

    def _build_fallback_report(
        self,
        vector_results: list[dict],
        payload: ComplianceReportRequest,
    ) -> ComplianceReportResponse:
        sources = [
            SourceCitation(
                source_id=f"doc:{item['document_id']}",
                source_type="vector_document",
                title=item["title"],
                url=item["source_url"],
                excerpt=item["chunk_text"][:240],
            )
            for item in vector_results
        ]

        if not sources:
            sources = [
                SourceCitation(
                    source_id="generated:no-results",
                    source_type="system_notice",
                    title="No matching regulatory seeds found",
                    excerpt=f"No local seed documents matched {payload.industry} in {payload.location}.",
                )
            ]

        primary_citation = [sources[0].source_id]
        compliance_items = [
            ComplianceRequirement(
                regulation_id=item["regulation_id"],
                certification_clause=(
                    f"{item['agency']} requirements apply to {payload.industry} operations in {payload.location}."
                ),
                business_activity="chemical inventory management",
                citations=[f"doc:{item['document_id']}"],
            )
            for item in vector_results[:3]
        ] or [
            ComplianceRequirement(
                regulation_id="TBD",
                certification_clause="Add regulatory seed data or live tool results to populate this section.",
                business_activity="compliance review",
                citations=primary_citation,
            )
        ]

        required_documents = []
        required_workflows = []
        seen_documents: set[str] = set()
        seen_workflows: set[str] = set()
        for item in vector_results:
            citation = [f"doc:{item['document_id']}"]
            for document_type in item["required_document_types"]:
                if document_type in seen_documents:
                    continue
                seen_documents.add(document_type)
                required_documents.append(
                    RequiredDocument(
                        document_type=document_type,
                        description=f"Maintain {document_type.lower()} aligned to {item['regulation_id']}.",
                        required_by=item["regulation_id"],
                        citations=citation,
                    )
                )
            for workflow_name in item["required_workflows"]:
                if workflow_name in seen_workflows:
                    continue
                seen_workflows.add(workflow_name)
                required_workflows.append(
                    RequiredWorkflow(
                        workflow_name=workflow_name,
                        description=f"Implement {workflow_name} controls for {payload.industry} operations.",
                        frequency="Defined by applicable regulation",
                        responsible_party="Compliance lead",
                        citations=citation,
                    )
                )

        regulatory_dependencies = [
            RegulatoryDependency(
                primary_agency="OSHA",
                related_agency="EPA",
                relationship="Process safety controls often overlap with EPA risk management planning obligations.",
                citations=primary_citation,
            )
        ]

        return ComplianceReportResponse(
            compliance_certification_requirements=compliance_items,
            regulatory_dependencies=regulatory_dependencies,
            required_documents=required_documents or [
                RequiredDocument(
                    document_type="Documentation gap",
                    description="Seed data did not provide document requirements for this profile.",
                    required_by="Seed dataset",
                    citations=primary_citation,
                )
            ],
            required_workflows=required_workflows or [
                RequiredWorkflow(
                    workflow_name="Workflow gap",
                    description="Seed data did not provide workflow requirements for this profile.",
                    frequency="TBD",
                    responsible_party="Compliance lead",
                    citations=primary_citation,
                )
            ],
            sources=sources,
        )
