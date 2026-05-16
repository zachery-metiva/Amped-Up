from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .dashboard_data import (
    CURRENT_USER,
    REPORTS,
    get_history,
    get_map_poles,
    get_open_reports,
    get_photos,
    get_pole_detail,
    get_summary,
)
from .dashboard_models import (
    AddNoteRequest,
    DashboardResponse,
    Note,
    ReportStatus,
    SelectedReport,
    UpdateReportStatusRequest,
    User,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

_notes: dict[str, list[Note]] = {}
_note_counter = 0


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


def _make_selected_report(report_id: str) -> tuple[SelectedReport | None, User]:
    for r in REPORTS:
        if r.id == report_id:
            submitter = User(
                initials=r.submitted_by.initials,
                name=r.submitted_by.name,
                role="Field tech",
                id=f"tech-{r.submitted_by.initials.lower()}",
            )
            return SelectedReport(
                id=r.id,
                pole_id=r.pole_id,
                title=r.title,
                severity=r.severity,
                submitted_by=submitter,
                submitted_at=r.submitted_at,
            ), submitter
    return None, CURRENT_USER


@router.get("", response_model=DashboardResponse)
def get_dashboard(selected_report_id: str | None = None) -> DashboardResponse:
    open_reports = get_open_reports()
    active_id = selected_report_id or (open_reports[0].id if open_reports else None)

    selected_report = None
    selected_pole = None
    photos: list = []
    history = None
    note_count = 0

    if active_id:
        selected_report, _ = _make_selected_report(active_id)
        if selected_report:
            selected_pole = get_pole_detail(selected_report.pole_id)
            photos = get_photos(selected_report.pole_id)
            history = get_history(selected_report.pole_id)
            note_count = len(_notes.get(active_id, []))

    return DashboardResponse(
        summary=get_summary(),
        reports=open_reports,
        map_poles=get_map_poles(),
        selected_report=selected_report,
        selected_pole=selected_pole,
        photos=photos,
        history=history,
        current_user=CURRENT_USER,
        note_count=note_count,
    )


@router.get("/reports/{report_id}/notes", response_model=list[Note])
def list_notes(report_id: str) -> list[Note]:
    return _notes.get(report_id, [])


@router.post("/reports/{report_id}/notes", response_model=Note)
async def add_note(report_id: str, body: AddNoteRequest) -> Note:
    global _note_counter
    _note_counter += 1
    note = Note(
        id=f"note-{_note_counter}",
        author=CURRENT_USER,
        content=body.content,
        created_at=datetime.now().isoformat(),
    )
    _notes.setdefault(report_id, []).append(note)
    await _manager.broadcast("note_added", {"report_id": report_id, "note": note.model_dump()})
    return note


@router.patch("/reports/{report_id}/status")
async def update_report_status(report_id: str, body: UpdateReportStatusRequest) -> dict[str, str]:
    for report in REPORTS:
        if report.id == report_id:
            report.status = body.status
            await _manager.broadcast(
                "report_status_changed",
                {"report_id": report_id, "status": body.status},
            )
            await _manager.broadcast("kpi_update", get_summary().model_dump())
            return {"status": "ok"}
    return {"status": "not_found"}


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await _manager.connect(ws)
    try:
        await ws.send_text(json.dumps({"event": "connected", "data": get_summary().model_dump()}))
        while True:
            text = await asyncio.wait_for(ws.receive_text(), timeout=30)
            msg = json.loads(text)
            if msg.get("type") == "ping":
                await ws.send_text(json.dumps({"event": "pong"}))
    except (WebSocketDisconnect, asyncio.TimeoutError, Exception):
        _manager.disconnect(ws)
