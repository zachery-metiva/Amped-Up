import { useEffect, useRef, useState } from 'react';
import { FieldPhotos } from '../components/FieldPhotos';
import { GridMap } from '../components/GridMap';
import { PoleDetails } from '../components/PoleDetails';
import { PoleHistory } from '../components/PoleHistory';
import { ReportBanner } from '../components/ReportBanner';
import { ReportNotes } from '../components/ReportNotes';
import {
  AllReportRow,
  DashboardData,
  FieldPhoto,
  MapPole,
  PoleHistory as PoleHistoryType,
  ReportStatus,
  Severity,
  User,
} from '../types';

const API = 'http://127.0.0.1:8000/api/dashboard';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function riskColor(score: number): string {
  if (score >= 58) return '#EF4444';
  if (score >= 40) return '#F97316';
  if (score >= 22) return '#FBBF24';
  return '#10B981';
}

function riskBand(score: number): string {
  if (score >= 58) return 'Critical';
  if (score >= 40) return 'High';
  if (score >= 22) return 'Medium';
  return 'Low';
}

const SEV_CLASS: Record<Severity, string> = {
  critical: 'sev-pill crit',
  high: 'sev-pill high',
  medium: 'sev-pill med',
  low: 'sev-pill low',
};

const SEV_LABEL: Record<Severity, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
};

const STAT_CLASS: Record<ReportStatus, string> = {
  open: 'stat-pill open',
  snoozed: 'stat-pill snoozed',
  approved: 'stat-pill approved',
  dismissed: 'stat-pill dismissed',
};

const STAT_LABEL: Record<ReportStatus, string> = {
  open: 'New',
  snoozed: 'Snoozed',
  approved: 'Approved',
  dismissed: 'Dismissed',
};

// ─── RiskBar ─────────────────────────────────────────────────────────────────

function RiskBar({ score }: { score: number | null }) {
  if (score === null) {
    return <span style={{ color: '#475569', fontSize: 11.5 }}>—</span>;
  }
  const color = riskColor(score);
  return (
    <div className="risk-bar">
      <div className="risk-bar-track">
        <div
          className="risk-bar-fill"
          style={{ width: `${score}%`, background: color }}
          aria-label={`Risk score ${score.toFixed(0)}`}
        />
      </div>
      <span className="risk-bar-score" style={{ color }}>{score.toFixed(0)}</span>
    </div>
  );
}

// ─── Filter state ─────────────────────────────────────────────────────────────

interface Filters {
  search: string;
  severities: Severity[];
  riskBands: string[]; // 'critical'|'high'|'medium'|'low' by score band
}

const EMPTY_FILTERS: Filters = { search: '', severities: [], riskBands: [] };

// ─── Detail View ─────────────────────────────────────────────────────────────

interface DetailData {
  dashData: DashboardData | null;
  loading: boolean;
}

type JsonObj = Record<string, unknown>;

function mapDetailData(raw: JsonObj): DashboardData {
  // Reuse the same mapping logic from useDashboard (inline for self-containment)
  const cu = raw.current_user as JsonObj;
  const currentUser: User = {
    initials: cu.initials as string,
    name: cu.name as string,
    role: cu.role as string,
    id: cu.id as string,
  };

  const sr = raw.selected_report as JsonObj | null;
  const selectedReport = sr
    ? {
        id: sr.id as string,
        poleId: sr.pole_id as string,
        title: sr.title as string,
        severity: sr.severity as Severity,
        submittedBy: {
          initials: (sr.submitted_by as JsonObj).initials as string,
          name: (sr.submitted_by as JsonObj).name as string,
          role: (sr.submitted_by as JsonObj).role as string,
          id: (sr.submitted_by as JsonObj).id as string,
        },
        submittedAt: sr.submitted_at as string,
      }
    : null;

  const sp = raw.selected_pole as JsonObj | null;
  const selectedPole = sp
    ? {
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
      }
    : null;

  const photos = ((raw.photos as JsonObj[]) ?? []).map(
    (p): FieldPhoto => ({
      id: p.id as string,
      label: p.label as string,
      imageUrl: p.image_url as string | null,
      severity: p.severity as Severity | null,
      severityLabel: p.severity_label as string | null,
    }),
  );

  const h = raw.history as JsonObj | null;
  const history: PoleHistoryType | null = h
    ? {
        poleId: h.pole_id as string,
        lifecycleYears: h.lifecycle_years as number | null,
        eventCount: h.event_count as number,
        commentCount: h.comment_count as number,
        events: ((h.events as JsonObj[]) ?? []).map((e) => {
          const author = e.author as JsonObj | null;
          return {
            id: e.id as string,
            type: e.type as import('../types').HistoryEventType,
            title: e.title as string,
            date: e.date as string | null,
            author: author
              ? { initials: author.initials as string, name: author.name as string }
              : null,
            description: e.description as string | null,
            comment: e.comment as string | null,
            severity: e.severity as Severity | null,
            pinColor: e.pin_color as string,
          };
        }),
      }
    : null;

  return {
    summary: {
      totalPoles: 0,
      recentCriticals: 0,
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      openReports: 0,
      sector: '',
      date: '',
    },
    reports: [],
    mapPoles: selectedPole
      ? [{ id: selectedPole.id, severity: selectedPole.severity, lat: selectedPole.lat, lon: selectedPole.lon }]
      : [],
    mapPoleCount: selectedPole ? 1 : 0,
    filters: {
      severities: [],
      classifications: [],
      circuits: [],
      owners: [],
      violationFamilies: [],
      violationTypes: [],
    },
    selectedReport,
    selectedPole,
    photos,
    history,
    currentUser,
    noteCount: raw.note_count as number,
  };
}

function ReportDetailView({
  reportId,
  poleId,
  onBack,
}: {
  reportId: string;
  poleId: string;
  onBack: () => void;
}) {
  const [detail, setDetail] = useState<DetailData>({ dashData: null, loading: true });
  const [riskFactors, setRiskFactors] = useState<Record<string, unknown> | null>(null);
  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [predictedSev, setPredictedSev] = useState<string | null>(null);

  // Fetch full detail data via the main dashboard endpoint
  useEffect(() => {
    setDetail({ dashData: null, loading: true });
    const params = new URLSearchParams({ selected_report_id: reportId });
    fetch(`${API}?${params}`)
      .then((r) => r.json())
      .then((json: JsonObj) => {
        setDetail({ dashData: mapDetailData(json), loading: false });
      })
      .catch(() => setDetail({ dashData: null, loading: false }));
  }, [reportId]);


  const { dashData, loading } = detail;

  async function handleUpdateStatus(status: string, note?: string) {
    await fetch(`${API}/reports/${reportId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, note: note ?? null }),
    });
    // Refetch detail
    const params = new URLSearchParams({ selected_report_id: reportId });
    const r = await fetch(`${API}?${params}`);
    const json = (await r.json()) as JsonObj;
    setDetail({ dashData: mapDetailData(json), loading: false });
  }

  async function handleUpdateSeverity(severity: Severity) {
    await fetch(`${API}/reports/${reportId}/severity`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ severity }),
    });
    const params = new URLSearchParams({ selected_report_id: reportId });
    const r = await fetch(`${API}?${params}`);
    const json = (await r.json()) as JsonObj;
    setDetail({ dashData: mapDetailData(json), loading: false });
  }

  async function handleAddNote(rid: string, content: string) {
    await fetch(`${API}/reports/${rid}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    const params = new URLSearchParams({ selected_report_id: reportId });
    const r = await fetch(`${API}?${params}`);
    const json = (await r.json()) as JsonObj;
    setDetail({ dashData: mapDetailData(json), loading: false });
  }

  if (loading) {
    return (
      <div className="ar-detail">
        <button className="ar-detail-back" onClick={onBack}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
          All reports
        </button>
        <div className="muted" style={{ textAlign: 'center', padding: '40px 0' }}>Loading report…</div>
      </div>
    );
  }

  if (!dashData) {
    return (
      <div className="ar-detail">
        <button className="ar-detail-back" onClick={onBack}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
          All reports
        </button>
        <div className="error-banner">Failed to load report detail.</div>
      </div>
    );
  }

  const { selectedReport, selectedPole, photos, history, currentUser, noteCount, mapPoles } = dashData;

  const mapPole: MapPole | null = selectedPole
    ? { id: selectedPole.id, severity: selectedPole.severity, lat: selectedPole.lat, lon: selectedPole.lon }
    : null;

  return (
    <div className="ar-detail">
      <button className="ar-detail-back" onClick={onBack}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="15 18 9 12 15 6" />
        </svg>
        All reports
      </button>

      {/* Report banner */}
      {selectedReport && (
        <ReportBanner
          report={selectedReport}
          onSeverityChange={handleUpdateSeverity}
          onDismiss={(note) => handleUpdateStatus('dismissed', note)}
          onApprove={(note) => handleUpdateStatus('approved', note)}
        />
      )}

      {/* Two-column detail layout */}
      <div className="ar-detail-two-col">
        {/* Left: mini map + pole details */}
        <div>
          {mapPole && (
            <div className="ar-map-mini" style={{ marginBottom: 14 }}>
              <GridMap
                poles={mapPoles}
                totalPoleCount={mapPoles.length}
                selectedPoleId={mapPole.id}
                onSelectPole={() => {}}
                riskPoles={[]}
              />
            </div>
          )}
          {selectedPole && <PoleDetails pole={selectedPole} />}
        </div>

        {/* Right: risk breakdown */}
        <RiskBreakdownCard
          poleId={poleId}
          riskScore={riskScore}
          predictedSev={predictedSev}
          riskFactors={riskFactors}
          onLoad={(score, sev, factors) => {
            setRiskScore(score);
            setPredictedSev(sev);
            setRiskFactors(factors);
          }}
        />
      </div>

      {/* Photos */}
      {photos.length > 0 && (
        <FieldPhotos photos={photos} inspectorLabel="Field photos" />
      )}

      {/* Notes */}
      {selectedReport && (
        <ReportNotes
          reportId={selectedReport.id}
          noteCount={noteCount}
          currentUser={currentUser}
          onAddNote={handleAddNote}
        />
      )}

      {/* History */}
      {history && <PoleHistory history={history} />}
    </div>
  );
}

// ─── Risk Breakdown Card ──────────────────────────────────────────────────────

const FACTOR_KEYS = ['vegetation', 'storm', 'flood', 'terrain', 'soil', 'age'];
const FACTOR_LABELS: Record<string, string> = {
  vegetation: 'Vegetation',
  storm: 'Storm',
  flood: 'Flood',
  terrain: 'Terrain',
  soil: 'Soil',
  age: 'Age',
};

function RiskBreakdownCard({
  poleId,
  riskScore,
  predictedSev,
  riskFactors,
  onLoad,
}: {
  poleId: string;
  riskScore: number | null;
  predictedSev: string | null;
  riskFactors: Record<string, unknown> | null;
  onLoad: (score: number | null, sev: string | null, factors: Record<string, unknown> | null) => void;
}) {
  const loadedRef = useRef(false);

  useEffect(() => {
    if (loadedRef.current) return;
    loadedRef.current = true;
    fetch(`${API}/risk-poles?limit=3000&min_score=0`)
      .then((r) => r.json())
      .then((json: JsonObj) => {
        const poles = (json.poles as JsonObj[]) ?? [];
        const found = poles.find((p) => (p.id as string) === poleId);
        if (found) {
          onLoad(
            (found.risk_score as number) ?? null,
            (found.predicted_severity as string) ?? null,
            (found.risk_factors as Record<string, unknown>) ?? null,
          );
        }
      })
      .catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [poleId]);

  const color = riskScore !== null ? riskColor(riskScore) : '#94A3B8';
  const band = riskScore !== null ? riskBand(riskScore) : null;

  return (
    <div className="ar-risk-card">
      <h4 style={{ marginBottom: 12 }}>Predictive risk</h4>

      {riskScore !== null ? (
        <>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 6 }}>
            <span className="ar-risk-score-big" style={{ color }}>{riskScore.toFixed(0)}</span>
            <span className="muted">/100</span>
          </div>
          {band && (
            <div style={{ marginBottom: 16 }}>
              <span className={`sev-pill ${band.toLowerCase() === 'critical' ? 'crit' : band.toLowerCase() === 'high' ? 'high' : band.toLowerCase() === 'medium' ? 'med' : 'low'}`}>
                {band} predicted risk
              </span>
              {predictedSev && (
                <span className="muted" style={{ marginLeft: 8 }}>
                  Predicted: {predictedSev.charAt(0).toUpperCase() + predictedSev.slice(1)}
                </span>
              )}
            </div>
          )}

          {riskFactors && (
            <>
              <div style={{ marginBottom: 8, fontSize: 11, color: 'var(--text-2)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
                Factor breakdown
              </div>
              {FACTOR_KEYS.map((key) => {
                const factor = riskFactors[key] as { score?: number; weight?: number } | undefined;
                if (!factor) return null;
                const score = factor.score ?? 0;
                const weight = factor.weight ?? 1;
                const contribution = score * weight;
                return (
                  <div key={key} className="ar-risk-factor-row">
                    <span className="ar-risk-factor-label">{FACTOR_LABELS[key]}</span>
                    <div className="ar-risk-factor-bar">
                      <div
                        className="ar-risk-factor-fill"
                        style={{ width: `${Math.min(contribution, 100)}%` }}
                      />
                    </div>
                    <span className="ar-risk-factor-score">{score.toFixed(0)}</span>
                  </div>
                );
              })}
            </>
          )}
        </>
      ) : (
        <div className="muted" style={{ padding: '20px 0' }}>
          No risk score computed for this pole.
        </div>
      )}
    </div>
  );
}

const LIMIT = 15;

// ─── Main AllReports component ────────────────────────────────────────────────

export function AllReports() {
  const [reports, setReports] = useState<AllReportRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [selectedPoleId, setSelectedPoleId] = useState<string | null>(null);

  // Fetch reports
  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    params.set('page', String(page));
    params.set('limit', String(LIMIT));
    if (filters.search.trim()) params.set('search', filters.search.trim());
    filters.severities.forEach((s) => params.append('severity', s));

    // Map risk bands to min_risk
    if (filters.riskBands.length === 1) {
      const band = filters.riskBands[0];
      const minMap: Record<string, number> = { critical: 58, high: 40, medium: 22, low: 0 };
      const min = minMap[band];
      if (min !== undefined) params.set('min_risk', String(min));
    }

    fetch(`${API}/all-reports?${params}`)
      .then((r) => r.json())
      .then((json: JsonObj) => {
        const rows = ((json.reports as JsonObj[]) ?? []).map(
          (r): AllReportRow => ({
            id: r.id as string,
            poleId: r.pole_id as string,
            title: r.title as string,
            severity: r.severity as Severity,
            status: r.status as ReportStatus,
            submittedAt: r.submitted_at as string,
            location: r.location as string,
            description: r.description as string | null,
            submittedBy: {
              initials: (r.submitted_by as JsonObj).initials as string,
              name: (r.submitted_by as JsonObj).name as string,
            },
            poleLat: r.pole_lat as number,
            poleLon: r.pole_lon as number,
            poleAddress: r.pole_address as string,
            poleClassification: r.pole_classification as string,
            poleCircuit: r.pole_circuit as string,
            riskScore: r.risk_score as number | null,
            predictedSeverity: r.predicted_severity as string | null,
          }),
        );
        setReports(rows);
        setTotal(json.total as number);
        setPage(json.page as number);
        setPages(json.pages as number);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [page, filters]);

  // Reset to page 1 when filters change
  const updateFilters = (next: Filters) => {
    setPage(1);
    setFilters(next);
  };

  const toggleSeverity = (sev: Severity) => {
    const next = filters.severities.includes(sev)
      ? filters.severities.filter((s) => s !== sev)
      : [...filters.severities, sev];
    updateFilters({ ...filters, severities: next });
  };

  const toggleRiskBand = (band: string) => {
    const next = filters.riskBands.includes(band)
      ? filters.riskBands.filter((b) => b !== band)
      : [...filters.riskBands, band];
    updateFilters({ ...filters, riskBands: next });
  };

  const hasFilters =
    filters.search.trim() || filters.severities.length > 0 || filters.riskBands.length > 0;
  const openCount = reports.filter((r) => r.status === 'open').length;

  function selectRow(row: AllReportRow) {
    setSelectedReportId(row.id);
    setSelectedPoleId(row.poleId);
  }

  // ── Detail view ──────────────────────────────────────────────────────────────
  if (selectedReportId && selectedPoleId) {
    return (
      <div className="ar-wrap">
        {/* Header */}
        <div className="ar-header">
          <div className="ar-logo">
            <div className="ar-logo-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBBF24" strokeWidth="2.2" aria-hidden="true">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
            </div>
            <span style={{ fontSize: 14, fontWeight: 600, color: '#F9FAFB' }}>Amped Up</span>
          </div>
          <div className="ar-breadcrumb">
            <button onClick={() => { window.location.href = '/evaluation'; }}>Dashboard</button>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6" /></svg>
            <button onClick={() => { setSelectedReportId(null); setSelectedPoleId(null); }}>All reports</button>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6" /></svg>
            <span>{selectedReportId}</span>
          </div>
        </div>

        <ReportDetailView
          reportId={selectedReportId}
          poleId={selectedPoleId}
          onBack={() => { setSelectedReportId(null); setSelectedPoleId(null); }}
        />
      </div>
    );
  }

  // ── Table / list view ────────────────────────────────────────────────────────
  return (
    <div className="ar-wrap">
      {/* Header */}
      <div className="ar-header">
        <div className="ar-logo">
          <div className="ar-logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FBBF24" strokeWidth="2.2" aria-hidden="true">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
          </div>
          <span style={{ fontSize: 14, fontWeight: 600, color: '#F9FAFB' }}>Amped Up</span>
        </div>
        <div className="ar-breadcrumb">
          <button onClick={() => { window.location.href = '/evaluation'; }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ verticalAlign: 'middle', marginRight: 3 }}><polyline points="15 18 9 12 15 6" /></svg>
            Dashboard
          </button>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6" /></svg>
          <span>All reports</span>
        </div>
      </div>

      <div className="ar-inner">
        {/* Title */}
        <div className="ar-title-row">
          <div>
            <h1 className="ar-title">All reports</h1>
            {!loading && (
              <p className="ar-subtitle">
                {total} total · {openCount} open
              </p>
            )}
          </div>
        </div>

        {/* Filter bar */}
        <div className="ar-filter-bar">
          {/* Search */}
          <div className="ar-search">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="search"
              placeholder="Search reports…"
              value={filters.search}
              onChange={(e) => updateFilters({ ...filters, search: e.target.value })}
              aria-label="Search reports"
            />
          </div>

          <div className="ar-divider" aria-hidden="true" />

          {/* Severity chips */}
          <span className="muted" style={{ fontSize: 11, whiteSpace: 'nowrap' }}>Severity:</span>
          {(['critical', 'high', 'medium', 'low'] as Severity[]).map((sev) => (
            <button
              key={sev}
              className={`ar-chip${filters.severities.includes(sev) ? ` active-${sev === 'critical' ? 'crit' : sev === 'medium' ? 'med' : sev}` : ''}`}
              onClick={() => toggleSeverity(sev)}
              aria-pressed={filters.severities.includes(sev)}
            >
              {SEV_LABEL[sev]}
            </button>
          ))}

          <div className="ar-divider" aria-hidden="true" />

          {/* Risk band chips */}
          <span className="muted" style={{ fontSize: 11, whiteSpace: 'nowrap' }}>Risk:</span>
          {[
            { key: 'critical', label: '≥58 Critical' },
            { key: 'high', label: '40–57 High' },
            { key: 'medium', label: '22–39 Medium' },
            { key: 'low', label: '<22 Low' },
          ].map(({ key, label }) => (
            <button
              key={key}
              className={`ar-chip${filters.riskBands.includes(key) ? ' active-risk' : ''}`}
              onClick={() => toggleRiskBand(key)}
              aria-pressed={filters.riskBands.includes(key)}
            >
              {label}
            </button>
          ))}

          {hasFilters && (
            <button
              className="ar-clear"
              onClick={() => updateFilters(EMPTY_FILTERS)}
            >
              Clear all
            </button>
          )}
        </div>

        {/* Table (desktop ≥901px) */}
        <div className="ar-table-wrap ar-table-desktop">
          {loading ? (
            <div className="muted" style={{ textAlign: 'center', padding: '40px 0' }}>Loading…</div>
          ) : reports.length === 0 ? (
            <div className="muted" style={{ textAlign: 'center', padding: '40px 0' }}>No reports found.</div>
          ) : (
            <table className="ar-table">
              <thead>
                <tr>
                  <th>Report ID</th>
                  <th>Pole &amp; Issue</th>
                  <th>Severity</th>
                  <th>Predictive risk</th>
                  <th>Submitted by</th>
                  <th>Location</th>
                  <th>Age</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((row) => (
                  <tr key={row.id} onClick={() => selectRow(row)} tabIndex={0} onKeyDown={(e) => e.key === 'Enter' && selectRow(row)}>
                    <td>
                      <span className="rid">{row.id}</span>
                      <div className="muted" style={{ marginTop: 2, fontSize: 11 }}>{row.poleId}</div>
                    </td>
                    <td style={{ maxWidth: 260 }}>
                      <div style={{ fontWeight: 500, color: '#F9FAFB', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {row.title}
                      </div>
                      <div className="muted" style={{ marginTop: 2, fontSize: 11 }}>{row.poleClassification}</div>
                    </td>
                    <td>
                      <span className={SEV_CLASS[row.severity]}>{SEV_LABEL[row.severity]}</span>
                    </td>
                    <td>
                      <RiskBar score={row.riskScore} />
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                        <div className="avatar" style={{ width: 22, height: 22, fontSize: 9 }}>
                          {row.submittedBy.initials}
                        </div>
                        <div>
                          <div style={{ color: '#F9FAFB', fontWeight: 500 }}>{row.submittedBy.name}</div>
                        </div>
                      </div>
                    </td>
                    <td style={{ maxWidth: 160 }}>
                      <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#94A3B8', fontSize: 11.5 }}>
                        {row.location}
                      </div>
                    </td>
                    <td style={{ whiteSpace: 'nowrap', color: '#94A3B8', fontSize: 11.5 }}>
                      {timeAgo(row.submittedAt)}
                    </td>
                    <td>
                      <span className={STAT_CLASS[row.status]}>{STAT_LABEL[row.status]}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Card rows (mobile/tablet <900px) */}
        <div className="ar-table-wrap ar-rows-mobile">
          {loading ? (
            <div className="muted" style={{ textAlign: 'center', padding: '40px 0' }}>Loading…</div>
          ) : reports.length === 0 ? (
            <div className="muted" style={{ textAlign: 'center', padding: '40px 0' }}>No reports found.</div>
          ) : (
            reports.map((row) => (
              <div key={row.id} className="ar-row" onClick={() => selectRow(row)} role="button" tabIndex={0} onKeyDown={(e) => e.key === 'Enter' && selectRow(row)}>
                <div className="ar-row-main">
                  <div className="ar-row-title">{row.title}</div>
                  <div className="ar-row-meta">
                    <span className="rid">{row.id}</span>
                    {' · '}
                    {row.poleId}
                    {' · '}
                    {timeAgo(row.submittedAt)}
                    {' · '}
                    {row.location}
                  </div>
                </div>
                <div className="ar-row-right">
                  <span className={SEV_CLASS[row.severity]}>{SEV_LABEL[row.severity]}</span>
                  <span className={STAT_CLASS[row.status]}>{STAT_LABEL[row.status]}</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        {pages > 1 && (
          <div className="ar-pagination">
            <button
              className="ar-page-btn"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              aria-label="Previous page"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
            </button>

            {Array.from({ length: Math.min(pages, 7) }, (_, i) => {
              let pageNum: number;
              if (pages <= 7) {
                pageNum = i + 1;
              } else if (page <= 4) {
                pageNum = i + 1;
              } else if (page >= pages - 3) {
                pageNum = pages - 6 + i;
              } else {
                pageNum = page - 3 + i;
              }
              return (
                <button
                  key={pageNum}
                  className={`ar-page-btn${pageNum === page ? ' active' : ''}`}
                  onClick={() => setPage(pageNum)}
                  aria-label={`Page ${pageNum}`}
                  aria-current={pageNum === page ? 'page' : undefined}
                >
                  {pageNum}
                </button>
              );
            })}

            <button
              className="ar-page-btn"
              disabled={page >= pages}
              onClick={() => setPage(page + 1)}
              aria-label="Next page"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6" /></svg>
            </button>

            <span className="ar-page-info">{page} of {pages}</span>
          </div>
        )}
      </div>
    </div>
  );
}
