from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import Regulation, RegulationVector


class VectorSearchTool:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search(self, query_embedding: list[float], filters: dict | None = None, top_k: int = 5) -> list[dict]:
        filters = filters or {}
        statement: Select = (
            select(RegulationVector, Regulation)
            .join(Regulation, Regulation.id == RegulationVector.regulation_id)
            .order_by(RegulationVector.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )

        if level := filters.get("level"):
            statement = statement.where(Regulation.level.ilike(level))
        if state := filters.get("state"):
            statement = statement.where(
                (Regulation.applies_to_all_states.is_(True)) | (Regulation.state.ilike(state))
            )
        if county := filters.get("county"):
            statement = statement.where(
                (Regulation.applies_to_all_counties.is_(True)) | (Regulation.county.ilike(county))
            )
        if city := filters.get("city_jurisdiction"):
            statement = statement.where(
                (Regulation.applies_to_all_cities.is_(True)) | (Regulation.city_jurisdiction.ilike(city))
            )
        if industry := filters.get("industry"):
            statement = statement.where(Regulation.industry.ilike(industry))
        if function := filters.get("function"):
            statement = statement.where(Regulation.function.ilike(function))

        rows = self.db.execute(statement).all()
        results: list[dict] = []
        for vector, regulation in rows:
            results.append(
                {
                    "regulation_id": regulation.id,
                    "regulation_name": regulation.regulation_name,
                    "regulation_code_reference": regulation.regulation_code_reference,
                    "level": regulation.level,
                    "state": regulation.state,
                    "county": regulation.county,
                    "city_jurisdiction": regulation.city_jurisdiction,
                    "description": regulation.description,
                    "action_required": regulation.action_required,
                    "search_text": vector.search_text,
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
