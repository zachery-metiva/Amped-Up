import { useCallback, useEffect, useRef, useState } from 'react';
import {
  DashboardData,
  DashboardFilterOptions,
  DashboardFilterState,
  DashboardSummary,
  FieldPhoto,
  HistoryEvent,
  HistoryEventType,
  MapPole,
  PoleDetail,
  PoleHistory,
  PredictedReport,
  Report,
  ReportAuthor,
  ReportStatus,
  RiskPole,
  RiskSummary,
  SelectedReport,
  Severity,
  User,
  WsPayload,
} from '../types';
import { DASHBOARD_API_URL, DASHBOARD_WS_URL } from '../config/api';
import { useWebSocket } from './useWebSocket';

const MAP_BATCH_SIZE = 1500;

type JsonObj = Record<string, unknown>;

export const EMPTY_DASHBOARD_FILTERS: DashboardFilterState = {
  severities: [],
  classifications: [],
  circuits: [],
  owners: [],
  violationFamilies: [],
  violationTypeIds: [],
};

function mapSummary(s: JsonObj): DashboardSummary {
  return {
    totalPoles: s.total_poles as number,
    recentCriticals: s.recent_criticals as number,
    critical: s.critical as number,
    high: s.high as number,
    medium: s.medium as number,
    low: s.low as number,
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
    mapNode: r.map_node ? mapMapPole(r.map_node as JsonObj) : null,
  };
}

function mapMapPole(p: JsonObj): MapPole {
  return {
    id: p.id as string,
    severity: p.severity as Severity,
    lat: p.lat as number,
    lon: p.lon as number,
  };
}

function mergeMapPoles(existing: MapPole[], incoming: MapPole[]): MapPole[] {
  const byId = new Map(existing.map((pole) => [pole.id, pole]));
  incoming.forEach((pole) => byId.set(pole.id, pole));
  return [...byId.values()];
}

function reportMapNodes(reports: Report[]): MapPole[] {
  return reports.map((report) => report.mapNode).filter((pole): pole is MapPole => Boolean(pole));
}

function appendFilterParams(params: URLSearchParams, activeFilters: DashboardFilterState, activeSearch: string) {
  if (activeSearch.trim()) params.set('search', activeSearch.trim());
  activeFilters.severities.forEach((value) => params.append('severity', value));
  activeFilters.classifications.forEach((value) => params.append('classification', value));
  activeFilters.circuits.forEach((value) => params.append('circuit', value));
  activeFilters.owners.forEach((value) => params.append('owner', value));
  activeFilters.violationFamilies.forEach((value) => params.append('violation_family', value));
  activeFilters.violationTypeIds.forEach((value) => params.append('violation_type_id', value));
}

function mapScopeKey(activeFilters: DashboardFilterState, activeSearch: string): string {
  return JSON.stringify({
    search: activeSearch.trim(),
    severities: activeFilters.severities,
    classifications: activeFilters.classifications,
    circuits: activeFilters.circuits,
    owners: activeFilters.owners,
    violationFamilies: activeFilters.violationFamilies,
    violationTypeIds: activeFilters.violationTypeIds,
  });
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
    imageUrl: p.image_url as string | null,
    severity: p.severity as Severity | null,
    severityLabel: p.severity_label as string | null,
  }));

  const reports = (raw.reports as JsonObj[]).map(mapReport);
  const mapPoles = mergeMapPoles(((raw.map_poles as JsonObj[]) ?? []).map(mapMapPole), reportMapNodes(reports));

  const rawFilters = raw.filters as JsonObj;
  const mapOption = (option: JsonObj) => ({
    value: option.value as string,
    label: option.label as string,
    count: option.count as number,
  });
  const filters: DashboardFilterOptions = {
    severities: ((rawFilters.severities as JsonObj[]) ?? []).map(mapOption),
    classifications: ((rawFilters.classifications as JsonObj[]) ?? []).map(mapOption),
    circuits: ((rawFilters.circuits as JsonObj[]) ?? []).map(mapOption),
    owners: ((rawFilters.owners as JsonObj[]) ?? []).map(mapOption),
    violationFamilies: ((rawFilters.violation_families as JsonObj[]) ?? []).map(mapOption),
    violationTypes: ((rawFilters.violation_types as JsonObj[]) ?? []).map(mapOption),
  };

  return {
    summary: mapSummary(raw.summary as JsonObj),
    reports,
    mapPoles,
    mapPoleCount: raw.map_pole_count as number,
    filters,
    selectedReport,
    selectedPole,
    photos,
    history,
    currentUser,
    noteCount: raw.note_count as number,
  };
}

function mapRiskPole(p: JsonObj): RiskPole {
  return {
    id: p.id as string,
    lat: p.lat as number,
    lon: p.lon as number,
    riskScore: p.risk_score as number,
    predictedSeverity: p.predicted_severity as Severity,
    riskFactors: (p.risk_factors as Record<string, unknown>) ?? null,
    riskComputedAt: (p.risk_computed_at as string) ?? null,
  };
}


function mapRiskSummary(raw: JsonObj, unscored = 0): RiskSummary {
  return {
    critical: (raw.critical as number) ?? 0,
    high: (raw.high as number) ?? 0,
    medium: (raw.medium as number) ?? 0,
    low: (raw.low as number) ?? 0,
    scored: (raw.scored as number) ?? 0,
    unscored,
    avgScore: ((raw.avg_score as number) || null),
  };
}

export function useDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [filters, setFilters] = useState<DashboardFilterState>(EMPTY_DASHBOARD_FILTERS);
  const [search, setSearch] = useState('');
  const [riskPoles, setRiskPoles] = useState<RiskPole[]>([]);
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [predictedReports, setPredictedReports] = useState<PredictedReport[]>([]);
  const selectedReportIdRef = useRef(selectedReportId);
  const mapFetchRunRef = useRef(0);
  const mapScopeKeyRef = useRef(mapScopeKey(filters, search));
  selectedReportIdRef.current = selectedReportId;

  const fetchDashboard = useCallback(async (reportId?: string | null, activeFilters = filters, activeSearch = search) => {
    const MAX_RETRIES = 3;
    const RETRY_DELAY_MS = 700;

    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
      try {
        const params = new URLSearchParams();
        if (reportId) params.set('selected_report_id', reportId);
        appendFilterParams(params, activeFilters, activeSearch);
        const qs = params.toString();
        const res = await fetch(`${DASHBOARD_API_URL}${qs ? `?${qs}` : ''}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = (await res.json()) as JsonObj;
        const next = mapResponse(json);
        const nextScopeKey = mapScopeKey(activeFilters, activeSearch);
        setData((prev) => {
          if (!prev || mapScopeKeyRef.current !== nextScopeKey) return next;
          return {
            ...next,
            mapPoles: mergeMapPoles(prev.mapPoles, next.mapPoles),
          };
        });
        setError(null);
        setLoading(false);
        return;
      } catch {
        if (attempt < MAX_RETRIES) {
          await new Promise<void>((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
        } else {
          setError('Backend not reachable. Check the API URL and backend service.');
          setLoading(false);
        }
      }
    }
  }, [filters, search]);

  useEffect(() => {
    fetchDashboard(selectedReportId, filters, search);
  }, [fetchDashboard, selectedReportId, filters, search]);

  const fetchMapPoles = useCallback(async (activeFilters = filters, activeSearch = search) => {
    const runId = ++mapFetchRunRef.current;
    const nextScopeKey = mapScopeKey(activeFilters, activeSearch);
    mapScopeKeyRef.current = nextScopeKey;
    let offset = 0;
    let loadedAll = false;

    setData((prev) => {
      if (!prev) return prev;
      return { ...prev, mapPoles: reportMapNodes(prev.reports) };
    });

    while (!loadedAll) {
      const params = new URLSearchParams();
      params.set('offset', String(offset));
      params.set('limit', String(MAP_BATCH_SIZE));
      appendFilterParams(params, activeFilters, activeSearch);

      const res = await fetch(`${DASHBOARD_API_URL}/map-poles?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = (await res.json()) as JsonObj;
      const batch = ((json.poles as JsonObj[]) ?? []).map(mapMapPole);
      const total = json.total as number;

      if (runId !== mapFetchRunRef.current) return;

      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          mapPoleCount: total,
          mapPoles: mergeMapPoles(prev.mapPoles, batch),
        };
      });

      offset += batch.length;
      loadedAll = batch.length < MAP_BATCH_SIZE || offset >= total;
    }
  }, [filters, search]);

  useEffect(() => {
    if (!data) return;
    fetchMapPoles(filters, search).catch(() => {
      setError('Backend not reachable. Map nodes could not be loaded.');
    });
  }, [data?.summary.date, filters, search, fetchMapPoles]);

  const fetchRiskLayer = useCallback(async () => {
    try {
      const [polesRes, summaryRes] = await Promise.all([
        fetch(`${DASHBOARD_API_URL}/risk-poles?limit=2000&min_score=0`),
        fetch(`${DASHBOARD_API_URL}/risk-summary`),
      ]);
      let unscored = 0;
      if (polesRes.ok) {
        const json = (await polesRes.json()) as JsonObj;
        const poles = ((json.poles as JsonObj[]) ?? []).map(mapRiskPole);
        unscored = (json.unscored as number) ?? 0;
        setRiskPoles(poles);
        // Derive predicted reports directly from scored poles — no separate table needed
        const derived: PredictedReport[] = poles.map((p) => ({
          id: `PRED-${p.id}`,
          poleId: p.id,
          title: `Predicted ${p.predictedSeverity} risk - ${p.id}`,
          predictedSeverity: p.predictedSeverity,
          riskScore: p.riskScore,
          riskFactors: p.riskFactors,
          status: 'open' as ReportStatus,
          generatedAt: p.riskComputedAt ?? new Date().toISOString(),
          lat: p.lat,
          lon: p.lon,
          classification: '',
          owner: '',
          circuit: '',
          address: '',
        }));
        setPredictedReports(derived);
      }
      if (summaryRes.ok) {
        const json = (await summaryRes.json()) as JsonObj;
        setRiskSummary(mapRiskSummary(json, unscored));
      }
    } catch {
      // Risk layer is best-effort — never block main dashboard
    }
  }, []);

  // Fetch risk layer once after the dashboard first loads (backend may not have scored poles yet)
  useEffect(() => {
    if (data) fetchRiskLayer();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [!!data]);

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
              recentCriticals: d.recent_criticals as number,
              critical: d.critical as number,
              high: d.high as number,
              medium: d.medium as number,
              low: d.low as number,
              openReports: d.open_reports as number,
            },
          };
        });
      } else if (payload.event === 'report_added') {
        const report = mapReport(payload.data as JsonObj);
        const hasActiveFilters =
          search.trim() ||
          filters.severities.length ||
          filters.classifications.length ||
          filters.circuits.length ||
          filters.owners.length ||
          filters.violationFamilies.length ||
          filters.violationTypeIds.length;

        if (hasActiveFilters) {
          fetchDashboard(selectedReportIdRef.current, filters, search);
          return;
        }

        setData((prev) => {
          if (!prev || prev.reports.some((existing) => existing.id === report.id)) return prev;
          return {
            ...prev,
            reports: [report, ...prev.reports],
            mapPoles: report.mapNode ? mergeMapPoles(prev.mapPoles, [report.mapNode]) : prev.mapPoles,
          };
        });
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
      } else if (payload.event === 'report_severity_changed') {
        fetchDashboard(selectedReportIdRef.current, filters, search);
      }
    },
    [fetchDashboard, filters, search],
  );

  const { connected } = useWebSocket(DASHBOARD_WS_URL, { onMessage: handleWsMessage });

  const selectReport = useCallback((reportId: string) => {
    setSelectedReportId(reportId);
  }, []);

  const addNote = useCallback(async (reportId: string, content: string) => {
    await fetch(`${DASHBOARD_API_URL}/reports/${reportId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
  }, []);

  const updateReportStatus = useCallback(async (reportId: string, status: ReportStatus, note?: string) => {
    await fetch(`${DASHBOARD_API_URL}/reports/${reportId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, note: note ?? null }),
    });
  }, []);

  const updateReportSeverity = useCallback(async (reportId: string, severity: Severity) => {
    await fetch(`${DASHBOARD_API_URL}/reports/${reportId}/severity`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ severity }),
    });
  }, []);

  const updateFilters = useCallback((next: DashboardFilterState) => {
    setFilters(next);
    setSelectedReportId(null);
  }, []);

  return {
    data,
    loading,
    error,
    connected,
    filters,
    setFilters: updateFilters,
    search,
    setSearch,
    selectReport,
    addNote,
    updateReportStatus,
    updateReportSeverity,
    riskPoles,
    riskSummary,
    predictedReports,
    refreshRiskLayer: fetchRiskLayer,
  };
}
