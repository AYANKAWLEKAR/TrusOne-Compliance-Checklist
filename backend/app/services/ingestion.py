from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk
from app.ingestion.chunking import chunk_text
from app.ingestion.embeddings import EmbeddingService
from app.schemas.ingest import SeedDocument


class IngestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.embeddings = EmbeddingService()

    async def ingest_documents(self, documents: list[SeedDocument]) -> int:
        inserted = 0
        for payload in documents:
            self.db.execute(delete(Document).where(Document.regulation_id == payload.regulation_id))
            document = Document(
                title=payload.title,
                source_url=payload.source_url,
                agency=payload.agency,
                regulation_id=payload.regulation_id,
                jurisdiction=payload.jurisdiction,
                state=payload.state,
                county=payload.county,
                industry_sectors=payload.industry_sectors,
                min_employee_size=payload.min_employee_size,
                max_employee_size=payload.max_employee_size,
                effective_date=payload.effective_date,
                full_text=payload.full_text,
                extra_metadata=payload.extra_metadata,
                required_document_types=payload.required_document_types,
                required_workflows=payload.required_workflows,
            )
            self.db.add(document)
            self.db.flush()

            for index, (chunk, token_count) in enumerate(chunk_text(payload.full_text)):
                embedding = await self.embeddings.embed(chunk)
                self.db.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=index,
                        chunk_text=chunk,
                        embedding=embedding,
                        token_count=token_count,
                    )
                )
            inserted += 1

        self.db.commit()
        return inserted
