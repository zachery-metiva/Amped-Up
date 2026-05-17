from __future__ import annotations

import asyncio
import json
import math
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import orm_models as dbm
from .database import SessionLocal, get_db
from .dashboard_data import (
    DashboardFilters,
    get_current_user,
    get_current_user_record,
    get_filter_options,
    get_history,
    get_map_pole_count,
    get_map_poles,
    get_note_count,
    get_notes,
    get_photos,
    get_pole_detail,
    get_reports,
    get_selected_report,
    get_summary,
)
from .osm_pole_data import GEOJSON_PATH
from .dashboard_models import (
    AddNoteRequest,
    AnalyzeRequest,
    AnalyzeResponse,
    AnalyzePhotosRequest,
    ComputeRiskResponse,
    DashboardResponse,
    MapPole,
    MapPolesResponse,
    Note,
    PhotoAnalysis,
    Report,
    ReportAuthor,
    ReportStatus,
    RiskPole,
    RiskPolesResponse,
    Severity,
    SubmitReportRequest,
    SynthesizeRequest,
    SynthesizeResponse,
    UpdateReportSeverityRequest,
    UpdateReportStatusRequest,
)
from .risk_engine import compute_pole_risk
from .photo_analysis import analyze_report_photos
from .watsonx_analyzer import VISION_MODEL_ID, get_analyzer

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _submitted_photo_data_urls(body: SubmitReportRequest) -> list[str]:
    return [photo.data_url for photo in body.photos if photo.data_url.startswith("data:image")]


def _utility_structure_validation(body: SubmitReportRequest) -> dict[str, Any]:
    photo_urls = _submitted_photo_data_urls(body)
    if not photo_urls:
        raise HTTPException(status_code=422, detail="Attach at least one photo of the utility pole or utility structure.")

    analyzer = get_analyzer()
    if not analyzer.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Watson vision validation is not configured, so this photo cannot be verified as a utility structure.",
        )

    try:
        validation = analyzer.analyze(
            description=body.description or "",
            pole_type=body.pole_type,
            photo_count=len(photo_urls),
            photos=photo_urls[:1],
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail="Watson vision validation failed, so this report was not submitted.",
        ) from exc
    if VISION_MODEL_ID not in str(validation.get("powered_by", "")):
        raise HTTPException(
            status_code=503,
            detail="Watson vision validation was unavailable, so this report was not submitted.",
        )
    if not validation.get("is_utility_structure", True):
        reason = validation.get("rejection_reason") or "The submitted image does not appear to contain a utility pole or utility structure."
        raise HTTPException(status_code=422, detail=reason)
    return validation


class _ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.remove(ws)

    async def broadcast(self, event: str, data: Any) -> None:
        payload = json.dumps({"event": event, "data": data})
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.remove(ws)


_manager = _ConnectionManager()


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    selected_report_id: str | None = None,
    severity: list[Severity] | None = Query(default=None),
    classification: list[str] | None = Query(default=None),
    circuit: list[str] | None = Query(default=None),
    owner: list[str] | None = Query(default=None),
    violation_family: list[str] | None = Query(default=None),
    violation_type_id: list[str] | None = Query(default=None),
    search: str | None = None,
    include_map: bool = False,
    db: Session = Depends(get_db),
) -> DashboardResponse:
    filters = DashboardFilters(
        severities=[dbm.Severity(value.value) for value in severity or []],
        classifications=classification,
        circuits=circuit,
        owners=owner,
        violation_families=violation_family,
        violation_type_ids=violation_type_id,
        search=search,
    )
    reports = get_reports(db, filters)
    active_report = next((report for report in reports if report.status == ReportStatus.OPEN), None)
    active_id = selected_report_id or (active_report.id if active_report else reports[0].id if reports else None)

    selected_report = None
    selected_pole = None
    photos: list = []
    history = None
    note_count = 0

    if active_id:
        selected_report = get_selected_report(db, active_id)
        if selected_report:
            selected_pole = get_pole_detail(db, selected_report.pole_id)
            photos = get_photos(db, selected_report.pole_id)
            history = get_history(db, selected_report.pole_id)
            note_count = get_note_count(db, active_id)

    return DashboardResponse(
        summary=get_summary(db, filters),
        reports=reports,
        map_poles=get_map_poles(db, filters) if include_map else [],
        map_pole_count=get_map_pole_count(db, filters) if include_map else 0,
        filters=get_filter_options(db, search),
        selected_report=selected_report,
        selected_pole=selected_pole,
        photos=photos,
        history=history,
        current_user=get_current_user(db),
        note_count=note_count,
    )


@router.get("/map-poles", response_model=MapPolesResponse)
def list_map_poles(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=1500, ge=1, le=7500),
    severity: list[Severity] | None = Query(default=None),
    classification: list[str] | None = Query(default=None),
    circuit: list[str] | None = Query(default=None),
    owner: list[str] | None = Query(default=None),
    violation_family: list[str] | None = Query(default=None),
    violation_type_id: list[str] | None = Query(default=None),
    search: str | None = None,
    db: Session = Depends(get_db),
) -> MapPolesResponse:
    filters = DashboardFilters(
        severities=[dbm.Severity(value.value) for value in severity or []],
        classifications=classification,
        circuits=circuit,
        owners=owner,
        violation_families=violation_family,
        violation_type_ids=violation_type_id,
        search=search,
    )
    return MapPolesResponse(
        poles=get_map_poles(db, filters, limit=limit, offset=offset),
        total=get_map_pole_count(db, filters),
        offset=offset,
        limit=limit,
    )


@router.get("/osm-poles.geojson")
def get_osm_poles_geojson() -> FileResponse:
    if not GEOJSON_PATH.exists():
        raise HTTPException(status_code=404, detail="DTE OSM pole GeoJSON not found")
    return FileResponse(GEOJSON_PATH, media_type="application/geo+json", filename=GEOJSON_PATH.name)


@router.get("/nearest-pole")
def get_nearest_pole(
    lat: float = Query(..., description="User latitude"),
    lon: float = Query(..., description="User longitude"),
    db: Session = Depends(get_db),
) -> dict:
    """Return the pole closest to the given coordinates using a flat-earth approximation."""
    cos_lat = math.cos(math.radians(lat))
    row = db.execute(
        select(
            dbm.Pole.id,
            dbm.Pole.latitude,
            dbm.Pole.longitude,
            dbm.Pole.severity,
            dbm.Pole.classification,
            dbm.Pole.owner,
            dbm.Pole.circuit,
            dbm.Pole.address,
        ).order_by(
            (dbm.Pole.latitude - lat) * (dbm.Pole.latitude - lat)
            + (dbm.Pole.longitude - lon) * (dbm.Pole.longitude - lon) * cos_lat * cos_lat
        ).limit(1)
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="No poles found")
    return {
        "pole_id":        row.id,
        "lat":            row.latitude,
        "lon":            row.longitude,
        "severity":       row.severity,
        "classification": row.classification,
        "owner":          row.owner,
        "circuit":        row.circuit,
        "address":        row.address,
    }


@router.get("/reports/{report_id}/notes", response_model=list[Note])
def list_notes(report_id: str, db: Session = Depends(get_db)) -> list[Note]:
    return get_notes(db, report_id)


@router.post("/reports/{report_id}/notes", response_model=Note)
async def add_note(
    report_id: str,
    body: AddNoteRequest,
    db: Session = Depends(get_db),
) -> Note:
    report = db.get(dbm.Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    current_user_record = get_current_user_record(db)
    if not current_user_record:
        raise HTTPException(status_code=409, detail="No users exist to author this note")

    note_row = dbm.ReportNote(
        id=f"note-{uuid4().hex[:12]}",
        report_id=report.id,
        author_user_id=current_user_record.id,
        content=body.content,
    )
    history_row = dbm.PoleHistoryEvent(
        id=f"evt-{uuid4().hex[:12]}",
        pole_id=report.pole_id,
        report_id=report.id,
        type=dbm.HistoryEventType.COMMENT,
        title=f"{current_user_record.name} - Comment on report {report.id}",
        event_date=None,
        author_user_id=current_user_record.id,
        description=None,
        comment=body.content,
        severity=None,
        pin_color="#475569",
    )
    db.add_all([note_row, history_row])
    db.commit()
    db.refresh(note_row)

    note = Note(
        id=note_row.id,
        author=get_current_user(db),
        content=note_row.content,
        created_at=note_row.created_at.isoformat(),
    )
    await _manager.broadcast("note_added", {"report_id": report_id, "note": note.model_dump(mode="json")})
    return note


@router.post("/reports", response_model=Report, status_code=201)
async def submit_report(
    body: SubmitReportRequest,
    db: Session = Depends(get_db),
) -> Report:
    field_user = db.get(dbm.User, "field-tech")
    if not field_user:
        field_user = dbm.User(id="field-tech", initials="FT", name="Field tech", role="Field technician")
        db.add(field_user)

    structure_validation = _utility_structure_validation(body)
    analysis = body.ai_analysis or analyze_report_photos(body.photos, body.description)
    analysis.is_utility_structure = bool(structure_validation.get("is_utility_structure", True))
    analysis.structure_confidence = int(structure_validation.get("structure_confidence", analysis.confidence))
    analysis.rejection_reason = structure_validation.get("rejection_reason")
    report_severity = dbm.Severity(body.severity.value if body.severity else analysis.severity.value)
    pole = db.get(dbm.Pole, body.pole_id)
    if not pole:
        pole = dbm.Pole(
            id=body.pole_id,
            classification=body.classification or body.pole_type or "Unknown",
            severity=report_severity,
            address=body.address or "Field-submitted location",
            latitude=body.location.lat if body.location else 0,
            longitude=body.location.lon if body.location else 0,
            owner=body.owner or "Unknown",
            circuit=body.circuit or "Unknown",
            ai_score=analysis.confidence,
            ai_confidence=f"{analysis.confidence}% confidence",
            recommendation=analysis.action,
        )
        db.add(pole)
    else:
        pole.severity = report_severity
        pole.ai_score = analysis.confidence
        pole.ai_confidence = f"{analysis.confidence}% confidence"
        pole.recommendation = analysis.action

    report_id = f"RPT-F-{uuid4().hex[:8].upper()}"
    submitted_at = datetime.now(timezone.utc)
    location_str = (
        f"{body.location.lat:.4f} N, {abs(body.location.lon):.4f} W"
        if body.location
        else "Location unavailable"
    )
    title_source = body.description or analysis.finding
    title = title_source[:60] if title_source else f"Field report - {body.photo_count} photo(s)"
    report_description = body.description.strip() if body.description else ""
    report_description = "\n".join(
        part
        for part in [
            report_description,
            f"AI summary: {analysis.finding}",
            f"Evidence required: {analysis.evidence_required}" if analysis.evidence_required else None,
            f"Regulatory references: {', '.join(analysis.regulations)}" if analysis.regulations else None,
            f"Utility structure validation: {analysis.structure_confidence}% confidence",
            f"Recommended action: {analysis.action}",
        ]
        if part
    )

    report_row = dbm.Report(
        id=report_id,
        pole_id=body.pole_id,
        title=title,
        severity=report_severity,
        status=dbm.ReportStatus.OPEN,
        violation_type_id=analysis.violation_type_id,
        submitted_by_user_id=field_user.id,
        submitted_at=submitted_at,
        location=body.address or location_str,
        description=report_description,
    )
    photo_rows = [
        dbm.FieldPhoto(
            id=f"photo-{uuid4().hex[:12]}",
            pole_id=body.pole_id,
            report_id=report_id,
            label=photo.label or f"Field photo {index}",
            image_url=photo.data_url,
            storage_key=None,
            severity=report_severity,
            severity_label=analysis.dashboard_title or f"AI {analysis.severity.value}",
            uploaded_by_user_id=field_user.id,
        )
        for index, photo in enumerate(body.photos, start=1)
    ]
    history_row = dbm.PoleHistoryEvent(
        id=f"evt-{uuid4().hex[:12]}",
        pole_id=body.pole_id,
        report_id=report_id,
        type=dbm.HistoryEventType.REPORT,
        title=f"Report {report_id} submitted by Field tech",
        event_date=submitted_at,
        author_user_id=field_user.id,
        description=f"{body.photo_count} photo(s) submitted. {analysis.finding}".strip(),
        comment=None,
        severity=report_severity,
        pin_color="#FBBF24",
    )
    db.add_all([report_row, *photo_rows, history_row])
    db.commit()
    db.refresh(report_row)

    # ── Feedback loop: calibrate risk score when actual AI severity differs ──
    if body.ai_analysis and pole.risk_score is not None and pole.predicted_severity is not None:
        sev_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        actual_ord = sev_order.get(body.ai_analysis.severity.lower(), 1)
        predicted_ord = sev_order.get(pole.predicted_severity.lower(), 1)
        delta = actual_ord - predicted_ord  # positive = under-predicted, negative = over-predicted
        # Nudge score: ±8 pts per severity step, clamped to [0, 100]
        if delta != 0:
            pole.risk_score = max(0.0, min(100.0, pole.risk_score + delta * 8.0))
            # Update factors dict to record the calibration
            factors = dict(pole.risk_factors or {})
            factors["_feedback"] = {
                "actual_severity": body.ai_analysis.severity,
                "predicted_severity": pole.predicted_severity,
                "delta_steps": delta,
                "calibrated_at": datetime.now(timezone.utc).isoformat(),
            }
            pole.risk_factors = factors
            db.commit()

    report = Report(
        id=report_row.id,
        pole_id=report_row.pole_id,
        title=report_row.title,
        severity=Severity(report_row.severity.value),
        submitted_by=ReportAuthor(initials=field_user.initials, name=field_user.name),
        submitted_at=report_row.submitted_at.isoformat(),
        location=report_row.location,
        status=ReportStatus.OPEN,
        map_node=MapPole(
            id=pole.id,
            severity=Severity(pole.severity.value),
            lat=pole.latitude,
            lon=pole.longitude,
        ),
    )
    await _manager.broadcast("report_added", report.model_dump(mode="json"))
    await _manager.broadcast("kpi_update", get_summary(db).model_dump(mode="json"))
    return report


@router.post("/reports/analyze", response_model=PhotoAnalysis)
def analyze_report_upload(body: AnalyzePhotosRequest) -> PhotoAnalysis:
    if not body.photos:
        return PhotoAnalysis(
            severity=Severity.LOW,
            finding="No photos were attached, so the report needs manual review.",
            confidence=40,
            nesc="NESC field review",
            action="Attach field photos or continue with a manual inspection note.",
            dashboard_title="Manual photo review",
            regulations=["NESC field review"],
            evidence_required="Attach field photos, pole type, location, and field notes.",
            specifications={"measurement_kind": "manual_review"},
        )
    return analyze_report_photos(body.photos, body.description)


@router.patch("/reports/{report_id}/status")
async def update_report_status(
    report_id: str,
    body: UpdateReportStatusRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    report = db.get(dbm.Report, report_id)
    if not report:
        return {"status": "not_found"}

    report.status = dbm.ReportStatus(body.status.value)

    # ── Audit trail: history event for every status transition ───────────────
    current_user_record = get_current_user_record(db)
    _STATUS_META: dict[str, tuple[str, str, str]] = {
        # status_value → (display title, HistoryEventType, pin_color)
        "approved":  ("Report approved",  "inspection", "#22C55E"),
        "dismissed": ("Report dismissed", "other",      "#94A3B8"),
        "snoozed":   ("Report snoozed",   "other",      "#F59E0B"),
        "open":      ("Report re-opened", "report",     "#3B82F6"),
    }
    meta = _STATUS_META.get(body.status.value)
    if meta:
        evt_title, evt_type_str, pin_color = meta
        history_row = dbm.PoleHistoryEvent(
            id=f"evt-{uuid4().hex[:12]}",
            pole_id=report.pole_id,
            report_id=report.id,
            type=dbm.HistoryEventType(evt_type_str),
            title=evt_title,
            event_date=datetime.now(timezone.utc),
            author_user_id=current_user_record.id if current_user_record else None,
            description=None,
            comment=body.note or None,
            severity=report.severity,
            pin_color=pin_color,
        )
        db.add(history_row)

        # If the evaluator supplied a note, also persist it as a ReportNote
        if body.note and body.note.strip() and current_user_record:
            note_row = dbm.ReportNote(
                id=f"note-{uuid4().hex[:12]}",
                report_id=report.id,
                author_user_id=current_user_record.id,
                content=body.note.strip(),
            )
            db.add(note_row)

    db.commit()

    await _manager.broadcast(
        "report_status_changed",
        {"report_id": report_id, "status": body.status.value},
    )
    await _manager.broadcast("kpi_update", get_summary(db).model_dump(mode="json"))
    return {"status": "ok"}


@router.patch("/reports/{report_id}/severity")
async def update_report_severity(
    report_id: str,
    body: UpdateReportSeverityRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    report = db.get(dbm.Report, report_id)
    if not report:
        return {"status": "not_found"}

    severity = dbm.Severity(body.severity.value)
    report.severity = severity
    if report.pole:
        report.pole.severity = severity
    db.commit()

    await _manager.broadcast(
        "report_severity_changed",
        {"report_id": report_id, "pole_id": report.pole_id, "severity": body.severity.value},
    )
    await _manager.broadcast("kpi_update", get_summary(db).model_dump(mode="json"))
    return {"status": "ok"}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_inspection(body: AnalyzeRequest) -> AnalyzeResponse:
    """
    Run watsonx.ai Granite analysis on a field inspection report.
    Returns severity classification, detected violations, NESC rules,
    and a recommended corrective action.
    Falls back to rule-based classification if the API key is not set.
    """
    analyzer = get_analyzer()
    result = analyzer.analyze(
        description=body.description,
        pole_type=body.pole_type,
        photo_count=body.photo_count,
        photos=body.photos,
    )
    # Normalise severity to the Severity enum (clamp unknown values to medium)
    raw_sev = result.get("severity", "medium")
    try:
        sev = Severity(raw_sev)
    except ValueError:
        sev = Severity.MEDIUM

    return AnalyzeResponse(
        severity=sev,
        violations=result.get("violations", []),
        osha_class=result.get("osha_class", "other_than_serious"),
        nesc_rules=result.get("nesc_rules", []),
        recommendation=result.get("recommendation", "Review and schedule corrective action"),
        ai_score=int(result.get("ai_score", 70)),
        confidence=result.get("confidence", "medium"),
        powered_by=result.get("powered_by", "watsonx.ai"),
        visual_observations=result.get("visual_observations") or None,
        is_utility_structure=bool(result.get("is_utility_structure", True)),
        structure_confidence=int(result.get("structure_confidence", result.get("ai_score", 70))),
        rejection_reason=result.get("rejection_reason"),
    )


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_analyses(body: SynthesizeRequest) -> SynthesizeResponse:
    """
    Combine N per-photo analyses of the same pole into one unified assessment.
    Uses ibm/granite-3-8b-instruct to produce a coherent narrative summary.
    """
    analyzer = get_analyzer()
    result = analyzer.synthesize(
        pole_id=body.pole_id,
        pole_type=body.pole_type,
        analyses=[a.model_dump() for a in body.analyses],
    )
    raw_sev = result.get("severity", "medium")
    try:
        sev = Severity(raw_sev)
    except ValueError:
        sev = Severity.MEDIUM

    return SynthesizeResponse(
        severity=sev,
        violations=result.get("violations", []),
        osha_class=result.get("osha_class", "other_than_serious"),
        nesc_rules=result.get("nesc_rules", []),
        recommendation=result.get("recommendation", "Review and schedule corrective action"),
        summary=result.get("summary", ""),
        ai_score=int(result.get("ai_score", 70)),
        confidence=result.get("confidence", "medium"),
        powered_by=result.get("powered_by", "watsonx.ai"),
    )


@router.get("/risk-poles", response_model=RiskPolesResponse)
def get_risk_poles(
    min_score: float = Query(0, ge=0, le=100),
    severity: str | None = None,
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db),
) -> RiskPolesResponse:
    """Return all poles that have a computed risk score, for the map risk layer."""
    q = select(dbm.Pole).where(dbm.Pole.risk_score.isnot(None))
    if min_score > 0:
        q = q.where(dbm.Pole.risk_score >= min_score)
    if severity:
        q = q.where(dbm.Pole.predicted_severity == severity)
    q = q.order_by(dbm.Pole.risk_score.desc()).limit(limit)
    poles = db.scalars(q).all()

    total_q = select(dbm.Pole)
    all_poles = db.scalars(total_q).all()
    unscored = sum(1 for p in all_poles if p.risk_score is None)

    return RiskPolesResponse(
        poles=[
            RiskPole(
                id=p.id,
                lat=p.latitude,
                lon=p.longitude,
                risk_score=p.risk_score,
                predicted_severity=dbm.Severity(p.predicted_severity),
                risk_factors=p.risk_factors,
                risk_computed_at=p.risk_computed_at.isoformat() if p.risk_computed_at else None,
            )
            for p in poles
        ],
        total=len(poles),
        unscored=unscored,
    )


@router.get("/risk-summary")
def get_risk_summary(db: Session = Depends(get_db)) -> dict:
    """Aggregate risk statistics across all scored poles."""
    poles = db.scalars(select(dbm.Pole).where(dbm.Pole.risk_score.isnot(None))).all()
    if not poles:
        return {"scored": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "avg_score": 0}
    counts: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for p in poles:
        if p.predicted_severity in counts:
            counts[p.predicted_severity] += 1
    avg = sum(p.risk_score for p in poles) / len(poles)
    return {
        "scored": len(poles),
        **counts,
        "avg_score": round(avg, 1),
    }


@router.post("/risk-poles/{pole_id}/compute", response_model=ComputeRiskResponse)
def compute_single_risk(pole_id: str, db: Session = Depends(get_db)) -> ComputeRiskResponse:
    """Compute and persist risk score for one pole (called on-demand)."""
    pole = db.get(dbm.Pole, pole_id)
    if not pole:
        raise HTTPException(status_code=404, detail="Pole not found")
    updates = compute_pole_risk(pole)
    for k, v in updates.items():
        setattr(pole, k, v)
    db.commit()
    return ComputeRiskResponse(
        pole_id=pole_id,
        risk_score=updates["risk_score"],
        predicted_severity=dbm.Severity(updates["predicted_severity"]),
        risk_factors=updates["risk_factors"],
    )


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await _manager.connect(ws)
    try:
        if SessionLocal is None:
            raise RuntimeError("DATABASE_URL is not set")
        with SessionLocal() as db:
            summary = get_summary(db).model_dump(mode="json")
        await ws.send_text(json.dumps({"event": "connected", "data": summary}))
        while True:
            text = await asyncio.wait_for(ws.receive_text(), timeout=30)
            msg = json.loads(text)
            if msg.get("type") == "ping":
                await ws.send_text(json.dumps({"event": "pong"}))
    except (WebSocketDisconnect, asyncio.TimeoutError, Exception):
        _manager.disconnect(ws)
