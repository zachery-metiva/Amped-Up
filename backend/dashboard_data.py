from __future__ import annotations

from .dashboard_models import (
    DashboardSummary,
    FieldPhoto,
    HistoryEvent,
    HistoryEventType,
    MapPole,
    PoleDetail,
    PoleHistory,
    Report,
    ReportAuthor,
    ReportStatus,
    Severity,
    User,
)

CURRENT_USER = User(
    initials="ZM",
    name="Z. Metiva",
    role="Field ops lead",
    id="user-001",
)

# Mutable list — status is updated in-place when reports are approved/dismissed/snoozed
REPORTS: list[Report] = [
    Report(
        id="RPT-1147",
        pole_id="P-1147",
        title="Lean exceeds 12°, crossarm rot",
        severity=Severity.CRITICAL,
        submitted_by=ReportAuthor(initials="JC", name="J. Chen"),
        submitted_at="2026-05-14T11:48:00",
        location="Michigan Ave & Trumbull Ave, Detroit",
        status=ReportStatus.OPEN,
    ),
    Report(
        id="RPT-1192",
        pole_id="P-1192",
        title="Transformer leak, oil stains",
        severity=Severity.CRITICAL,
        submitted_by=ReportAuthor(initials="DK", name="D. Kim"),
        submitted_at="2026-05-14T08:30:00",
        location="W. Vernor Hwy & Rosa Parks Blvd, Detroit",
        status=ReportStatus.OPEN,
    ),
    Report(
        id="RPT-1062",
        pole_id="P-1062",
        title="Woodpecker damage, upper third",
        severity=Severity.HIGH,
        submitted_by=ReportAuthor(initials="AS", name="A. Singh"),
        submitted_at="2026-05-13T09:15:00",
        location="W. Willis St & 13th St, Detroit",
        status=ReportStatus.OPEN,
    ),
    Report(
        id="RPT-1078",
        pole_id="P-1078",
        title="Insulator cracked, phase B",
        severity=Severity.HIGH,
        submitted_by=ReportAuthor(initials="MR", name="M. Reyes"),
        submitted_at="2026-05-13T14:22:00",
        location="Michigan Ave & 15th St, Detroit",
        status=ReportStatus.OPEN,
    ),
    Report(
        id="RPT-1023",
        pole_id="P-1023",
        title="Vegetation contact, secondary",
        severity=Severity.MEDIUM,
        submitted_by=ReportAuthor(initials="TB", name="T. Brown"),
        submitted_at="2026-05-12T16:05:00",
        location="Temple St & Trumbull Ave, Detroit",
        status=ReportStatus.OPEN,
    ),
    Report(
        id="RPT-1131",
        pole_id="P-1131",
        title="Guy wire tension below spec",
        severity=Severity.MEDIUM,
        submitted_by=ReportAuthor(initials="LW", name="L. Williams"),
        submitted_at="2026-05-11T10:44:00",
        location="W. Grand Blvd & 14th St, Detroit",
        status=ReportStatus.OPEN,
    ),
]

_POLE_DETAILS: dict[str, PoleDetail] = {
    "P-1147": PoleDetail(
        id="P-1147",
        classification="Class 3 Southern Pine",
        severity=Severity.CRITICAL,
        address="Michigan Ave & Trumbull Ave, Detroit, MI",
        lat=42.3321,
        lon=-83.0478,
        height="45 ft (above grade 38 ft)",
        owner="DTE Energy · Joint use with Comcast",
        circuit="Feeder F-407 · 13.2 kV",
        lean="12.4° (spec ≤ 5°)",
        ai_score=94,
        ai_confidence="high confidence",
        recommendation="Replace within 7 days",
    ),
    "P-1192": PoleDetail(
        id="P-1192",
        classification="Class 2 Southern Pine",
        severity=Severity.CRITICAL,
        address="W. Vernor Hwy & Rosa Parks Blvd, Detroit, MI",
        lat=42.3298,
        lon=-83.0456,
        height="40 ft (above grade 34 ft)",
        owner="DTE Energy",
        circuit="Feeder F-312 · 13.2 kV",
        lean=None,
        ai_score=88,
        ai_confidence="high confidence",
        recommendation="Dispatch hazmat and replace transformer",
    ),
    "P-1062": PoleDetail(
        id="P-1062",
        classification="Class 3 Southern Pine",
        severity=Severity.HIGH,
        address="W. Willis St & 13th St, Detroit, MI",
        lat=42.3339,
        lon=-83.0462,
        height="45 ft (above grade 37 ft)",
        owner="DTE Energy",
        circuit="Feeder F-501 · 13.2 kV",
        lean=None,
        ai_score=76,
        ai_confidence="medium confidence",
        recommendation="Inspect and treat within 30 days",
    ),
    "P-1078": PoleDetail(
        id="P-1078",
        classification="Class 4 Southern Pine",
        severity=Severity.HIGH,
        address="Michigan Ave & 15th St, Detroit, MI",
        lat=42.3315,
        lon=-83.0510,
        height="35 ft (above grade 28 ft)",
        owner="DTE Energy",
        circuit="Feeder F-407 · 13.2 kV",
        lean=None,
        ai_score=71,
        ai_confidence="medium confidence",
        recommendation="Replace insulator within 30 days",
    ),
    "P-1023": PoleDetail(
        id="P-1023",
        classification="Class 3 Southern Pine",
        severity=Severity.MEDIUM,
        address="Temple St & Trumbull Ave, Detroit, MI",
        lat=42.3352,
        lon=-83.0481,
        height="45 ft (above grade 38 ft)",
        owner="DTE Energy",
        circuit="Feeder F-501 · 13.2 kV",
        lean=None,
        ai_score=54,
        ai_confidence="medium confidence",
        recommendation="Schedule vegetation trim within 90 days",
    ),
    "P-1131": PoleDetail(
        id="P-1131",
        classification="Class 3 Steel",
        severity=Severity.MEDIUM,
        address="W. Grand Blvd & 14th St, Detroit, MI",
        lat=42.3374,
        lon=-83.0498,
        height="50 ft (above grade 43 ft)",
        owner="DTE Energy",
        circuit="Feeder F-312 · 13.2 kV",
        lean=None,
        ai_score=58,
        ai_confidence="medium confidence",
        recommendation="Re-tension guy wire within 90 days",
    ),
}

_PHOTOS: dict[str, list[FieldPhoto]] = {
    "P-1147": [
        FieldPhoto(id="photo-1", label="01 · Overview, west", severity=Severity.CRITICAL, severity_label="12° lean"),
        FieldPhoto(id="photo-2", label="02 · Crossarm closeup", severity=Severity.CRITICAL, severity_label="Rot"),
        FieldPhoto(id="photo-3", label="03 · Transformer base", severity=Severity.MEDIUM, severity_label="Oil staining"),
    ],
    "P-1192": [
        FieldPhoto(id="photo-4", label="01 · Overview, north", severity=Severity.CRITICAL, severity_label="Oil leak"),
        FieldPhoto(id="photo-5", label="02 · Transformer base", severity=Severity.CRITICAL, severity_label="Staining"),
    ],
}

_HISTORIES: dict[str, PoleHistory] = {
    "P-1147": PoleHistory(
        pole_id="P-1147",
        lifecycle_years=18,
        event_count=6,
        comment_count=2,
        events=[
            HistoryEvent(
                id="evt-1",
                type=HistoryEventType.REPORT,
                title="Report RPT-1147 submitted by J. Chen",
                date="2026-05-14T11:48:00",
                author=ReportAuthor(initials="JC", name="J. Chen"),
                description="3 photos uploaded. 12° lean and crossarm rot called out. AI scored 94, classified Critical. Pending crew assignment.",
                comment=None,
                severity=Severity.CRITICAL,
                pin_color="#EF4444",
            ),
            HistoryEvent(
                id="evt-2",
                type=HistoryEventType.COMMENT,
                title="R. Patel · Comment on report UP-2026-04891",
                date="2026-05-14T15:42:00",
                author=ReportAuthor(initials="RP", name="R. Patel"),
                description=None,
                comment="Crew 14 dispatched for tomorrow 7 AM. Bringing a 45 ft Class 3 replacement and the lift truck. Traffic permit cleared with MDOT.",
                severity=None,
                pin_color="#475569",
            ),
            HistoryEvent(
                id="evt-3",
                type=HistoryEventType.COMMENT,
                title="J. Liu · Comment on report UP-2026-04891",
                date="2026-05-14T13:08:00",
                author=ReportAuthor(initials="JL", name="J. Liu"),
                description=None,
                comment="De-energize feeder F-407 before approach. Comcast fiber attached at 23 ft, coordinate with their NOC ticket 88421.",
                severity=None,
                pin_color="#475569",
            ),
            HistoryEvent(
                id="evt-4",
                type=HistoryEventType.INSPECTION,
                title="Routine inspection · drone",
                date="2025-11-02",
                author=None,
                description="Last manual check. Minor lean noted (4.8°). Vegetation trimmed.",
                comment=None,
                severity=None,
                pin_color="#FBBF24",
            ),
            HistoryEvent(
                id="evt-5",
                type=HistoryEventType.UPGRADE,
                title="Hardware upgrade",
                date="2022-08-19",
                author=None,
                description="Transformer swapped from 25 kVA to 50 kVA. Polymer insulators installed.",
                comment=None,
                severity=None,
                pin_color="#60A5FA",
            ),
            HistoryEvent(
                id="evt-6",
                type=HistoryEventType.JOINT_USE,
                title="Joint use added",
                date="2019-03-04",
                author=None,
                description="Comcast fiber attachment permitted at 23 ft above grade.",
                comment=None,
                severity=None,
                pin_color="#60A5FA",
            ),
            HistoryEvent(
                id="evt-7",
                type=HistoryEventType.TREATMENT,
                title="Treatment cycle",
                date="2014-06-12",
                author=None,
                description="CCA pressure-treatment refresh. Estimated remaining life 22 years.",
                comment=None,
                severity=None,
                pin_color="#10B981",
            ),
            HistoryEvent(
                id="evt-8",
                type=HistoryEventType.INSTALL,
                title="Pole installed",
                date="2008-04-27",
                author=None,
                description="Class 3 Southern Pine, 45 ft. Original contractor Quanta Services.",
                comment=None,
                severity=None,
                pin_color="#6B7280",
            ),
        ],
    ),
    # Example pole with unknown install date — lifecycle_years and install event date are None
    "P-1192": PoleHistory(
        pole_id="P-1192",
        lifecycle_years=None,
        event_count=2,
        comment_count=0,
        events=[
            HistoryEvent(
                id="evt-9",
                type=HistoryEventType.REPORT,
                title="Report RPT-1192 submitted by D. Kim",
                date="2026-05-14T08:30:00",
                author=ReportAuthor(initials="DK", name="D. Kim"),
                description="Transformer oil leak observed. Significant staining on pole base and surrounding ground.",
                comment=None,
                severity=Severity.CRITICAL,
                pin_color="#EF4444",
            ),
            HistoryEvent(
                id="evt-10",
                type=HistoryEventType.INSTALL,
                title="Pole installed",
                date=None,  # install date unknown
                author=None,
                description=None,
                comment=None,
                severity=None,
                pin_color="#6B7280",
            ),
        ],
    ),
}

_MAP_POLES: list[MapPole] = [
    # Poles with full detail records — coordinates must match _POLE_DETAILS above
    MapPole(id="P-1147", severity=Severity.CRITICAL, lat=42.3321, lon=-83.0478),
    MapPole(id="P-1192", severity=Severity.CRITICAL, lat=42.3298, lon=-83.0456),
    MapPole(id="P-1062", severity=Severity.HIGH,     lat=42.3339, lon=-83.0462),
    MapPole(id="P-1078", severity=Severity.HIGH,     lat=42.3315, lon=-83.0510),
    MapPole(id="P-1023", severity=Severity.MEDIUM,   lat=42.3352, lon=-83.0481),
    MapPole(id="P-1131", severity=Severity.MEDIUM,   lat=42.3374, lon=-83.0498),
    # Additional poles distributed through Detroit Corktown / Midtown district
    MapPole(id="P-1001", severity=Severity.LOW,    lat=42.3365, lon=-83.0520),
    MapPole(id="P-1002", severity=Severity.LOW,    lat=42.3380, lon=-83.0445),
    MapPole(id="P-1003", severity=Severity.LOW,    lat=42.3302, lon=-83.0490),
    MapPole(id="P-1004", severity=Severity.LOW,    lat=42.3290, lon=-83.0515),
    MapPole(id="P-1005", severity=Severity.MEDIUM, lat=42.3345, lon=-83.0435),
    MapPole(id="P-1006", severity=Severity.LOW,    lat=42.3275, lon=-83.0468),
    MapPole(id="P-1007", severity=Severity.LOW,    lat=42.3395, lon=-83.0455),
    MapPole(id="P-1008", severity=Severity.LOW,    lat=42.3280, lon=-83.0500),
    MapPole(id="P-1009", severity=Severity.LOW,    lat=42.3388, lon=-83.0525),
]


def get_summary() -> DashboardSummary:
    open_count = sum(1 for r in REPORTS if r.status == ReportStatus.OPEN)
    return DashboardSummary(
        total_poles=248,
        new_since_last_scan=12,
        critical=7,
        high=14,
        medium=31,
        open_reports=open_count,
        sector="D-7",
        date="2026-05-14",
    )


def get_open_reports() -> list[Report]:
    return [r for r in REPORTS if r.status == ReportStatus.OPEN]


def get_pole_detail(pole_id: str) -> PoleDetail | None:
    return _POLE_DETAILS.get(pole_id)


def get_photos(pole_id: str) -> list[FieldPhoto]:
    return _PHOTOS.get(pole_id, [])


def get_history(pole_id: str) -> PoleHistory | None:
    return _HISTORIES.get(pole_id)


def get_map_poles() -> list[MapPole]:
    return _MAP_POLES
