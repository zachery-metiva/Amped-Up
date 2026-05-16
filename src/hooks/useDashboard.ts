import { useCallback, useEffect, useRef, useState } from 'react';
import {
  DashboardData,
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
  SelectedReport,
  Severity,
  User,
  WsPayload,
} from '../types';
import { useWebSocket } from './useWebSocket';

const API = 'http://127.0.0.1:8000/api/dashboard';
const WS_URL = 'ws://127.0.0.1:8000/api/dashboard/ws';

type JsonObj = Record<string, unknown>;

function mapSummary(s: JsonObj): DashboardSummary {
  return {
    totalPoles: s.total_poles as number,
    newSinceLastScan: s.new_since_last_scan as number,
    critical: s.critical as number,
    high: s.high as number,
    medium: s.medium as number,
    openReports: s.open_reports as number,
    sector: s.sector as string,
    date: s.date as string,
  };
}

function mapReport(r: JsonObj): Report {
  const by = r.submitted_by as JsonObj;
  return {
    id: r.id as string,
    poleId: r.pole_id as string,
    title: r.title as string,
    severity: r.severity as Severity,
    submittedBy: { initials: by.initials as string, name: by.name as string },
    submittedAt: r.submitted_at as string,
    location: r.location as string,
    status: r.status as ReportStatus,
  };
}

function mapSelectedReport(sr: JsonObj): SelectedReport {
  const by = sr.submitted_by as JsonObj;
  return {
    id: sr.id as string,
    poleId: sr.pole_id as string,
    title: sr.title as string,
    severity: sr.severity as Severity,
    submittedBy: {
      initials: by.initials as string,
      name: by.name as string,
      role: by.role as string,
      id: by.id as string,
    },
    submittedAt: sr.submitted_at as string,
  };
}

function mapPoleDetail(sp: JsonObj): PoleDetail {
  return {
    id: sp.id as string,
    classification: sp.classification as string,
    severity: sp.severity as Severity,
    address: sp.address as string,
    lat: sp.lat as number,
    lon: sp.lon as number,
    height: sp.height as string,
    owner: sp.owner as string,
    circuit: sp.circuit as string,
    lean: sp.lean as string | null,
    aiScore: sp.ai_score as number,
    aiConfidence: sp.ai_confidence as string,
    recommendation: sp.recommendation as string,
  };
}

function mapHistoryEvent(e: JsonObj): HistoryEvent {
  const author = e.author as JsonObj | null;
  return {
    id: e.id as string,
    type: e.type as HistoryEventType,
    title: e.title as string,
    date: e.date as string | null,
    author: author
      ? ({ initials: author.initials as string, name: author.name as string } satisfies ReportAuthor)
      : null,
    description: e.description as string | null,
    comment: e.comment as string | null,
    severity: e.severity as Severity | null,
    pinColor: e.pin_color as string,
  };
}

function mapHistory(h: JsonObj): PoleHistory {
  return {
    poleId: h.pole_id as string,
    lifecycleYears: h.lifecycle_years as number | null,
    eventCount: h.event_count as number,
    commentCount: h.comment_count as number,
    events: (h.events as JsonObj[]).map(mapHistoryEvent),
  };
}

function mapResponse(raw: JsonObj): DashboardData {
  const cu = raw.current_user as JsonObj;
  const currentUser: User = {
    initials: cu.initials as string,
    name: cu.name as string,
    role: cu.role as string,
    id: cu.id as string,
  };

  const selectedReport = raw.selected_report
    ? mapSelectedReport(raw.selected_report as JsonObj)
    : null;

  const selectedPole = raw.selected_pole
    ? mapPoleDetail(raw.selected_pole as JsonObj)
    : null;

  const history = raw.history
    ? mapHistory(raw.history as JsonObj)
    : null;

  const photos = (raw.photos as JsonObj[]).map((p): FieldPhoto => ({
    id: p.id as string,
    label: p.label as string,
    severity: p.severity as Severity | null,
    severityLabel: p.severity_label as string | null,
  }));

  const mapPoles = (raw.map_poles as JsonObj[]).map((p): MapPole => ({
    id: p.id as string,
    severity: p.severity as Severity,
    lat: p.lat as number,
    lon: p.lon as number,
  }));

  return {
    summary: mapSummary(raw.summary as JsonObj),
    reports: (raw.reports as JsonObj[]).map(mapReport),
    mapPoles,
    selectedReport,
    selectedPole,
    photos,
    history,
    currentUser,
    noteCount: raw.note_count as number,
  };
}

export function useDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const selectedReportIdRef = useRef(selectedReportId);
  selectedReportIdRef.current = selectedReportId;

  const fetchDashboard = useCallback(async (reportId?: string | null) => {
    try {
      const params = reportId ? `?selected_report_id=${reportId}` : '';
      const res = await fetch(`${API}${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = (await res.json()) as JsonObj;
      setData(mapResponse(json));
      setError(null);
    } catch {
      setError('Backend not reachable — start FastAPI on port 8000.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard(selectedReportId);
  }, [fetchDashboard, selectedReportId]);

  const handleWsMessage = useCallback(
    (payload: WsPayload) => {
      if (payload.event === 'kpi_update') {
        const d = payload.data as JsonObj;
        setData((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            summary: {
              ...prev.summary,
              critical: d.critical as number,
              high: d.high as number,
              medium: d.medium as number,
              openReports: d.open_reports as number,
            },
          };
        });
      } else if (payload.event === 'report_added') {
        fetchDashboard(selectedReportIdRef.current);
      } else if (payload.event === 'note_added') {
        const d = payload.data;
        setData((prev) => {
          if (!prev || prev.selectedReport?.id !== d.report_id) return prev;
          return { ...prev, noteCount: prev.noteCount + 1 };
        });
      } else if (payload.event === 'report_status_changed') {
        const { report_id, status } = payload.data;
        setData((prev) => {
          if (!prev) return prev;
          const reports = prev.reports.filter((r) => r.id !== report_id);
          // When the active report is closed, clear it so the UI falls back gracefully
          const selectedReport =
            prev.selectedReport?.id === report_id && status !== 'open'
              ? null
              : prev.selectedReport;
          return { ...prev, reports, selectedReport };
        });
      }
    },
    [fetchDashboard],
  );

  const { connected } = useWebSocket(WS_URL, { onMessage: handleWsMessage });

  const selectReport = useCallback((reportId: string) => {
    setSelectedReportId(reportId);
  }, []);

  const addNote = useCallback(async (reportId: string, content: string) => {
    await fetch(`${API}/reports/${reportId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
  }, []);

  const updateReportStatus = useCallback(async (reportId: string, status: ReportStatus) => {
    await fetch(`${API}/reports/${reportId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
  }, []);

  return { data, loading, error, connected, selectReport, addNote, updateReportStatus };
}
