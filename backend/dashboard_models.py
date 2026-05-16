from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


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
    new_since_last_scan: int
    critical: int
    high: int
    medium: int
    open_reports: int
    sector: str
    date: str


class Report(BaseModel):
    id: str
    pole_id: str
    title: str
    severity: Severity
    submitted_by: ReportAuthor
    submitted_at: str
    location: str
    status: ReportStatus


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
    lean: str | None  # None when unknown or within spec
    ai_score: int
    ai_confidence: str
    recommendation: str


class FieldPhoto(BaseModel):
    id: str
    label: str
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
    date: str | None  # None when installation or maintenance date is unknown
    author: ReportAuthor | None
    description: str | None
    comment: str | None  # populated only for comment-type events
    severity: Severity | None
    pin_color: str


class PoleHistory(BaseModel):
    pole_id: str
    lifecycle_years: int | None  # None when install date is unknown
    event_count: int
    comment_count: int
    events: list[HistoryEvent]


class MapPole(BaseModel):
    id: str
    severity: Severity
    lat: float
    lon: float


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    reports: list[Report]
    map_poles: list[MapPole]
    selected_report: SelectedReport | None
    selected_pole: PoleDetail | None
    photos: list[FieldPhoto]
    history: PoleHistory | None
    current_user: User
    note_count: int


class AddNoteRequest(BaseModel):
    content: str


class UpdateReportStatusRequest(BaseModel):
    status: ReportStatus
