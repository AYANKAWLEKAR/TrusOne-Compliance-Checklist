from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.ingest import DocumentIngestRequest, IngestResponse
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


@router.post("/documents", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_documents(
    payload: DocumentIngestRequest,
    db: Session = Depends(get_db),
) -> IngestResponse:
    service = IngestionService(db)
    inserted = await service.ingest_documents(payload.documents)
    return IngestResponse(inserted_documents=inserted)
