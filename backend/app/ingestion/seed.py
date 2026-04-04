from __future__ import annotations

import asyncio

from app.db.session import SessionLocal
from app.schemas.ingest import SeedDocument
from app.services.ingestion import IngestionService
from app.ingestion.seed_data import SEED_DOCUMENTS


async def main() -> None:
    db = SessionLocal()
    try:
        service = IngestionService(db)
        documents = [SeedDocument.model_validate(item) for item in SEED_DOCUMENTS]
        await service.ingest_documents(documents)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
