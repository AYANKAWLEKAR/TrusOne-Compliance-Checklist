from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.compliance import (
    ComplianceOptionsResponse,
    ComplianceReportRequest,
    ComplianceReportResponse,
)
from app.services.compliance import ComplianceReportService

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


@router.post("/report", response_model=ComplianceReportResponse)
async def generate_report(
    payload: ComplianceReportRequest,
    db: Session = Depends(get_db),
) -> ComplianceReportResponse:
    service = ComplianceReportService(db)
    return await service.generate_report(payload)


@router.get("/options", response_model=ComplianceOptionsResponse)
async def list_compliance_options(
    db: Session = Depends(get_db),
) -> ComplianceOptionsResponse:
    service = ComplianceReportService(db)
    return service.list_options()
