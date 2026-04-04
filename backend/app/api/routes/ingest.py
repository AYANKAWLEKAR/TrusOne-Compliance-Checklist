from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.ingest import WorkbookIngestRequest, WorkbookIngestResponse
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


@router.post("/regulations/workbook", response_model=WorkbookIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_regulation_workbook(
    payload: WorkbookIngestRequest,
    db: Session = Depends(get_db),
) -> WorkbookIngestResponse:
    service = IngestionService(db)
    result = await service.ingest_regulation_workbook(payload.workbook_path)
    return WorkbookIngestResponse(**result)
