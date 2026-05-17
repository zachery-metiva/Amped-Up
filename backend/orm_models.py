from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


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


severity_enum = Enum(Severity, name="severity", values_callable=lambda values: [item.value for item in values])
report_status_enum = Enum(
    ReportStatus,
    name="report_status",
    values_callable=lambda values: [item.value for item in values],
)
history_event_type_enum = Enum(
    HistoryEventType,
    name="history_event_type",
    values_callable=lambda values: [item.value for item in values],
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    initials: Mapped[str] = mapped_column(String(8), nullable=False)
    role: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    submitted_reports: Mapped[list[Report]] = relationship(back_populates="submitted_by")
    notes: Mapped[list[ReportNote]] = relationship(back_populates="author")
    uploaded_photos: Mapped[list[FieldPhoto]] = relationship(back_populates="uploaded_by")
    history_events: Mapped[list[PoleHistoryEvent]] = relationship(back_populates="author")


class Pole(Base):
    __tablename__ = "poles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    classification: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[Severity] = mapped_column(severity_enum, nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    height_ft: Mapped[float | None] = mapped_column(Float)
    above_grade_ft: Mapped[float | None] = mapped_column(Float)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    circuit: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    lean_degrees: Mapped[float | None] = mapped_column(Float)
    lean_status: Mapped[str | None] = mapped_column(String(120))
    ai_score: Mapped[int | None] = mapped_column(Integer)
    ai_confidence: Mapped[str | None] = mapped_column(String(80))
    recommendation: Mapped[str | None] = mapped_column(Text)
    sector: Mapped[str | None] = mapped_column(String(40), index=True)
    installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Predictive risk profiling
    risk_score: Mapped[float | None] = mapped_column(Float, index=True)
    predicted_severity: Mapped[str | None] = mapped_column(String(16), index=True)
    risk_factors: Mapped[dict | None] = mapped_column(JSON)
    risk_computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    reports: Mapped[list[Report]] = relationship(back_populates="pole", cascade="all, delete-orphan")
    photos: Mapped[list[FieldPhoto]] = relationship(back_populates="pole", cascade="all, delete-orphan")
    history_events: Mapped[list[PoleHistoryEvent]] = relationship(back_populates="pole", cascade="all, delete-orphan")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pole_id: Mapped[str] = mapped_column(ForeignKey("poles.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[Severity] = mapped_column(severity_enum, nullable=False, index=True)
    status: Mapped[ReportStatus] = mapped_column(report_status_enum, nullable=False, default=ReportStatus.OPEN, index=True)
    violation_type_id: Mapped[str | None] = mapped_column(ForeignKey("violation_types.id"), index=True)
    submitted_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    pole: Mapped[Pole] = relationship(back_populates="reports")
    violation_type: Mapped[ViolationType | None] = relationship(back_populates="reports")
    submitted_by: Mapped[User] = relationship(back_populates="submitted_reports")
    notes: Mapped[list[ReportNote]] = relationship(back_populates="report", cascade="all, delete-orphan")
    photos: Mapped[list[FieldPhoto]] = relationship(back_populates="report")
    history_events: Mapped[list[PoleHistoryEvent]] = relationship(back_populates="report")


class ReportNote(Base):
    __tablename__ = "report_notes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    author_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    report: Mapped[Report] = relationship(back_populates="notes")
    author: Mapped[User] = relationship(back_populates="notes")


class FieldPhoto(Base):
    __tablename__ = "field_photos"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pole_id: Mapped[str] = mapped_column(ForeignKey("poles.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id: Mapped[str | None] = mapped_column(ForeignKey("reports.id", ondelete="SET NULL"), index=True)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text)
    storage_key: Mapped[str | None] = mapped_column(String(255))
    severity: Mapped[Severity | None] = mapped_column(severity_enum, index=True)
    severity_label: Mapped[str | None] = mapped_column(String(120))
    uploaded_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pole: Mapped[Pole] = relationship(back_populates="photos")
    report: Mapped[Report | None] = relationship(back_populates="photos")
    uploaded_by: Mapped[User | None] = relationship(back_populates="uploaded_photos")


class PoleHistoryEvent(Base):
    __tablename__ = "pole_history_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pole_id: Mapped[str] = mapped_column(ForeignKey("poles.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id: Mapped[str | None] = mapped_column(ForeignKey("reports.id", ondelete="SET NULL"), index=True)
    type: Mapped[HistoryEventType] = mapped_column(history_event_type_enum, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    author_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    comment: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[Severity | None] = mapped_column(severity_enum, index=True)
    pin_color: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pole: Mapped[Pole] = relationship(back_populates="history_events")
    report: Mapped[Report | None] = relationship(back_populates="history_events")
    author: Mapped[User | None] = relationship(back_populates="history_events")


class ViolationType(Base):
    __tablename__ = "violation_types"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    default_severity: Mapped[Severity | None] = mapped_column(severity_enum, index=True)
    recommended_action: Mapped[str | None] = mapped_column(Text)
    standard_org: Mapped[str] = mapped_column(String(80), default="IEEE", nullable=False)
    standard_code: Mapped[str] = mapped_column(String(80), default="IEEE C2", nullable=False)
    standard_name: Mapped[str] = mapped_column(String(160), default="National Electrical Safety Code", nullable=False)
    edition_year: Mapped[int] = mapped_column(Integer, default=2023, nullable=False, index=True)
    nesc_part: Mapped[str | None] = mapped_column(String(160), index=True)
    nesc_section: Mapped[str | None] = mapped_column(String(160))
    rule_number: Mapped[str | None] = mapped_column(String(40), index=True)
    subrule: Mapped[str | None] = mapped_column(String(40))
    table_number: Mapped[str | None] = mapped_column(String(40), index=True)
    violation_family: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    measurement_kind: Mapped[str | None] = mapped_column(String(80))
    measurement_unit: Mapped[str | None] = mapped_column(String(40))
    comparator: Mapped[str | None] = mapped_column(String(16))
    threshold_value: Mapped[float | None] = mapped_column(Float)
    applicability: Mapped[dict | None] = mapped_column(JSON)
    evidence_required: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    reports: Mapped[list[Report]] = relationship(back_populates="violation_type")
