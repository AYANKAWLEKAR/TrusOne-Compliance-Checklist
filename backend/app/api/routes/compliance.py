from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.compliance import ComplianceReportRequest, ComplianceReportResponse
from app.services.compliance import ComplianceReportService

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


@router.post("/report", response_model=ComplianceReportResponse)
async def generate_report(
    payload: ComplianceReportRequest,
    db: Session = Depends(get_db),
) -> ComplianceReportResponse:
    service = ComplianceReportService(db)
    return await service.generate_report(payload)
