from __future__ import annotations

from enum import StrEnum

from pydantic import AliasChoices, BaseModel, Field


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReportStatus(StrEnum):
    OPEN = "open"
    SNOOZED = "snoozed"
    APPROVED = "approved"
    DISMISSED = "dismissed"


class HistoryEventType(StrEnum):
    REPORT = "report"
    COMMENT = "comment"
    INSPECTION = "inspection"
    UPGRADE = "upgrade"
    JOINT_USE = "joint_use"
    TREATMENT = "treatment"
    INSTALL = "install"
    OTHER = "other"


class ReportAuthor(BaseModel):
    initials: str
    name: str


class User(BaseModel):
    initials: str
    name: str
    role: str
    id: str


class DashboardSummary(BaseModel):
    total_poles: int
    recent_criticals: int
    critical: int
    high: int
    medium: int
    low: int
    open_reports: int
    sector: str
    date: str


class MapPole(BaseModel):
    id: str
    severity: Severity
    lat: float
    lon: float
    risk_score: float | None = None
    predicted_severity: str | None = None


class Report(BaseModel):
    id: str
    pole_id: str
    title: str
    severity: Severity
    submitted_by: ReportAuthor
    submitted_at: str
    location: str
    status: ReportStatus
    map_node: MapPole | None = None


class SelectedReport(BaseModel):
    id: str
    pole_id: str
    title: str
    severity: Severity
    submitted_by: User
    submitted_at: str


class PoleDetail(BaseModel):
    id: str
    classification: str
    severity: Severity
    address: str
    lat: float
    lon: float
    height: str
    owner: str
    circuit: str
    lean: str | None
    ai_score: int
    ai_confidence: str
    recommendation: str


class FieldPhoto(BaseModel):
    id: str
    label: str
    image_url: str | None
    severity: Severity | None
    severity_label: str | None


class Note(BaseModel):
    id: str
    author: User
    content: str
    created_at: str


class HistoryEvent(BaseModel):
    id: str
    type: HistoryEventType
    title: str
    date: str | None
    author: ReportAuthor | None
    description: str | None
    comment: str | None
    severity: Severity | None
    pin_color: str


class PoleHistory(BaseModel):
    pole_id: str
    lifecycle_years: int | None
    event_count: int
    comment_count: int
    events: list[HistoryEvent]


class FilterOption(BaseModel):
    value: str
    label: str
    count: int


class DashboardFilterOptions(BaseModel):
    severities: list[FilterOption]
    classifications: list[FilterOption]
    circuits: list[FilterOption]
    owners: list[FilterOption]
    violation_families: list[FilterOption]
    violation_types: list[FilterOption]


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    reports: list[Report]
    map_poles: list[MapPole]
    map_pole_count: int
    filters: DashboardFilterOptions
    selected_report: SelectedReport | None
    selected_pole: PoleDetail | None
    photos: list[FieldPhoto]
    history: PoleHistory | None
    current_user: User
    note_count: int


class MapPolesResponse(BaseModel):
    poles: list[MapPole]
    total: int
    offset: int
    limit: int


class AddNoteRequest(BaseModel):
    content: str


class UpdateReportStatusRequest(BaseModel):
    status: ReportStatus
    note: str | None = None   # optional evaluator note written on status change


class UpdateReportSeverityRequest(BaseModel):
    severity: Severity


class AnalyzeRequest(BaseModel):
    pole_id: str
    pole_type: str | None = None
    description: str = ""
    photo_count: int = 0
    address: str | None = None
    photos: list[str] | None = None


class AnalyzeResponse(BaseModel):
    severity: Severity
    violations: list[str]
    osha_class: str
    nesc_rules: list[str]
    recommendation: str
    ai_score: int
    confidence: str
    powered_by: str
    visual_observations: list[str] | None = None
    is_utility_structure: bool = True
    structure_confidence: int = 70
    rejection_reason: str | None = None


class GpsLocation(BaseModel):
    lat: float
    lon: float
    accuracy: float


class PhotoAnalysisInput(BaseModel):
    photo_label: str
    severity: Severity
    violations: list[str]
    osha_class: str
    nesc_rules: list[str]
    recommendation: str
    ai_score: int


class SynthesizeRequest(BaseModel):
    pole_id: str
    pole_type: str | None = None
    analyses: list[PhotoAnalysisInput]


class SynthesizeResponse(BaseModel):
    severity: Severity
    violations: list[str]
    osha_class: str
    nesc_rules: list[str]
    recommendation: str
    summary: str
    ai_score: int
    confidence: str
    powered_by: str


class SubmittedPhoto(BaseModel):
    id: str
    label: str
    data_url: str = Field(validation_alias=AliasChoices("data_url", "dataUrl"))


class PhotoAnalysis(BaseModel):
    severity: Severity
    finding: str
    confidence: int
    nesc: str
    action: str
    violation_type_id: str | None = None
    violation_code: str | None = None
    violation_family: str | None = None
    dashboard_title: str | None = None
    regulations: list[str] = Field(default_factory=list)
    evidence_required: str | None = None
    specifications: dict[str, str | int | float | None] = Field(default_factory=dict)
    is_utility_structure: bool = True
    structure_confidence: int = 70
    rejection_reason: str | None = None


class AnalyzePhotosRequest(BaseModel):
    photos: list[SubmittedPhoto]
    description: str | None = None


class SubmitReportRequest(BaseModel):
    pole_id: str
    location: GpsLocation | None
    description: str
    photo_count: int
    photos: list[SubmittedPhoto] = Field(default_factory=list)
    ai_analysis: PhotoAnalysis | None = None
    pole_type: str | None = None
    classification: str | None = None
    owner: str | None = None
    circuit: str | None = None
    address: str | None = None
    severity: Severity | None = None


class RiskFactor(BaseModel):
    score: float
    weight: float
    label: str
    evidence: str | None = None


class RiskPole(BaseModel):
    id: str
    lat: float
    lon: float
    risk_score: float
    predicted_severity: Severity
    risk_factors: dict | None = None
    risk_computed_at: str | None = None


class PredictedReport(BaseModel):
    id: str
    pole_id: str
    title: str
    predicted_severity: Severity
    risk_score: float
    risk_factors: dict | None = None
    status: ReportStatus
    generated_at: str
    lat: float
    lon: float
    classification: str
    owner: str
    circuit: str
    address: str


class PredictedReportsResponse(BaseModel):
    reports: list[PredictedReport]
    total: int
    open_count: int


class RiskPolesResponse(BaseModel):
    poles: list[RiskPole]
    total: int
    unscored: int


class ComputeRiskResponse(BaseModel):
    pole_id: str
    risk_score: float
    predicted_severity: Severity
    risk_factors: dict
