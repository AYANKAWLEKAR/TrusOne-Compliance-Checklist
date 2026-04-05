from pydantic import BaseModel, Field, model_validator

from app.schemas.common import CitationBearingModel, SourceCitation


class ComplianceReportRequest(BaseModel):
    location: str = Field(..., min_length=1)
    industry: str = Field(..., min_length=1)
    company_size: str = Field(..., min_length=1)
    compliance_status: str | None = Field(default=None)
    location_city: str | None = Field(default=None)
    location_county: str | None = Field(default=None)
    location_state: str | None = Field(default=None)


class ComplianceLocationOption(BaseModel):
    value: str = Field(..., min_length=1)
    display_label: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    county: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
    aliases: list[str] = Field(default_factory=list)


class ComplianceOptionsResponse(BaseModel):
    industries: list[str] = Field(default_factory=list)
    locations: list[ComplianceLocationOption] = Field(default_factory=list)


class ComplianceReportSummary(BaseModel):
    analysis_text: str = Field(..., min_length=1)
    total_tasks: int = Field(..., ge=0)
    completed_tasks: int = Field(..., ge=0)
    open_tasks: int = Field(..., ge=0)
    mapped_sources: list[str] = Field(default_factory=list)


class TaskDetail(BaseModel):
    explanation: str = Field(..., min_length=1)
    next_step: str = Field(..., min_length=1)
    why_it_matters: str = Field(..., min_length=1)
    notes: str = Field(..., min_length=1)


class TaskItem(CitationBearingModel):
    id: str = Field(..., pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    source_url: str | None = None
    priority_label: str = Field(..., min_length=1)
    meta_label: str = Field(..., min_length=1)
    default_completed: bool = False
    detail: TaskDetail


class ComplianceTaskSynthesis(BaseModel):
    summary: ComplianceReportSummary
    tasks: list[TaskItem]


class ComplianceReportResponse(BaseModel):
    summary: ComplianceReportSummary
    tasks: list[TaskItem]
    sources: list[SourceCitation]

    @model_validator(mode="after")
    def validate_payload(self) -> "ComplianceReportResponse":
        source_ids = {source.source_id for source in self.sources}
        for task in self.tasks:
            missing = [citation for citation in task.citations if citation not in source_ids]
            if missing:
                raise ValueError(f"Unknown citations referenced: {missing}")

        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for task in self.tasks if task.default_completed)
        open_tasks = total_tasks - completed_tasks

        if self.summary.total_tasks != total_tasks:
            raise ValueError("summary.total_tasks must match the number of tasks.")
        if self.summary.completed_tasks != completed_tasks:
            raise ValueError("summary.completed_tasks must match completed task count.")
        if self.summary.open_tasks != open_tasks:
            raise ValueError("summary.open_tasks must match open task count.")

        return self
