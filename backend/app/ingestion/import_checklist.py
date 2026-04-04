from __future__ import annotations

import asyncio
import sys

from app.db.session import SessionLocal
from app.services.ingestion import IngestionService


async def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m app.ingestion.import_checklist /path/to/checklist.xlsx")

    workbook_path = sys.argv[1]
    db = SessionLocal()
    try:
        service = IngestionService(db)
        result = await service.ingest_regulation_workbook(workbook_path)
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
