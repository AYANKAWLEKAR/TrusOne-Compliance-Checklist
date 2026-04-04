from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import Regulation, RegulationVector
from app.ingestion.chunking import count_tokens
from app.ingestion.embeddings import EmbeddingService
from app.ingestion.workbook import ChecklistRow, parse_checklist_workbook, regulation_search_text


def _applies_to_all(value: str) -> bool:
    return value.strip().lower() == "all"


def _jurisdiction_scope(level: str) -> str:
    return level.strip().lower()


class IngestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.embeddings = EmbeddingService()

    async def ingest_regulation_workbook(self, workbook_path: str) -> dict[str, int]:
        rows = parse_checklist_workbook(workbook_path)
        inserted = 0
        updated = 0
        inserted_vectors = 0

        for row in rows:
            regulation, created = self._upsert_regulation(row)
            if created:
                inserted += 1
            else:
                updated += 1

            self.db.execute(delete(RegulationVector).where(RegulationVector.regulation_id == regulation.id))
            search_text = regulation_search_text(row)
            embedding = await self.embeddings.embed(search_text)
            self.db.add(
                RegulationVector(
                    regulation_id=regulation.id,
                    search_text=search_text,
                    embedding=embedding,
                    token_count=count_tokens(search_text),
                )
            )
            inserted_vectors += 1

        self.db.commit()
        return {
            "parsed_regulations": len(rows),
            "inserted_regulations": inserted,
            "updated_regulations": updated,
            "inserted_vectors": inserted_vectors,
        }

    def _upsert_regulation(self, row: ChecklistRow) -> tuple[Regulation, bool]:
        statement = select(Regulation).where(
            Regulation.industry == row.industry,
            Regulation.function == row.function,
            Regulation.state == row.state,
            Regulation.county == row.county,
            Regulation.city_jurisdiction == row.city_jurisdiction,
            Regulation.level == row.level,
            Regulation.regulation_code_reference == row.regulation_code_reference,
        )
        regulation = self.db.execute(statement).scalar_one_or_none()
        created = regulation is None

        values = {
            "industry": row.industry,
            "function": row.function,
            "state": row.state,
            "county": row.county,
            "city_jurisdiction": row.city_jurisdiction,
            "level": row.level,
            "jurisdiction_scope": _jurisdiction_scope(row.level),
            "applies_to_all_states": _applies_to_all(row.state),
            "applies_to_all_counties": _applies_to_all(row.county),
            "applies_to_all_cities": _applies_to_all(row.city_jurisdiction),
            "regulation_name": row.regulation_name,
            "regulation_code_reference": row.regulation_code_reference,
            "description": row.description,
            "action_required": row.action_required,
            "external_metadata": None,
        }

        if regulation is None:
            regulation = Regulation(**values)
            self.db.add(regulation)
            self.db.flush()
        else:
            for key, value in values.items():
                setattr(regulation, key, value)
            self.db.flush()

        return regulation, created
