from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk


class VectorSearchTool:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search(self, query_embedding: list[float], filters: dict | None = None, top_k: int = 5) -> list[dict]:
        filters = filters or {}
        statement: Select = (
            select(DocumentChunk, Document)
            .join(Document, Document.id == DocumentChunk.document_id)
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )

        if jurisdiction := filters.get("jurisdiction"):
            statement = statement.where(Document.jurisdiction == jurisdiction)
        if state := filters.get("state"):
            statement = statement.where(Document.state == state)
        if county := filters.get("county"):
            statement = statement.where(Document.county == county)
        if industry := filters.get("industry"):
            statement = statement.where(Document.industry_sectors.any(industry))
        if company_size := filters.get("company_size"):
            minimum, maximum = self._parse_company_size(company_size)
            if minimum is not None:
                statement = statement.where(
                    (Document.max_employee_size.is_(None)) | (Document.max_employee_size >= minimum)
                )
            if maximum is not None:
                statement = statement.where(
                    (Document.min_employee_size.is_(None)) | (Document.min_employee_size <= maximum)
                )

        rows = self.db.execute(statement).all()
        results: list[dict] = []
        for chunk, document in rows:
            results.append(
                {
                    "document_id": document.id,
                    "title": document.title,
                    "regulation_id": document.regulation_id,
                    "source_url": document.source_url,
                    "agency": document.agency,
                    "chunk_text": chunk.chunk_text,
                    "required_document_types": document.required_document_types,
                    "required_workflows": document.required_workflows,
                }
            )
        return results

    @staticmethod
    def _parse_company_size(company_size: str) -> tuple[int | None, int | None]:
        normalized = company_size.strip()
        if "+" in normalized:
            return int(normalized.replace("+", "")), None
        if "-" in normalized:
            start, end = normalized.split("-", maxsplit=1)
            return int(start), int(end)
        return None, None
