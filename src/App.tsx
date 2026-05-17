import { FieldPhotos } from './components/FieldPhotos';
import { DashboardFilters } from './components/DashboardFilters';
import { GridMap } from './components/GridMap';
import { Header } from './components/Header';
import { HeaderSearch } from './components/HeaderSearch';
import { IncomingReports } from './components/IncomingReports';
import { KpiCards } from './components/KpiCards';
import { PoleDetails } from './components/PoleDetails';
import { PoleHistory } from './components/PoleHistory';
import { ReportBanner } from './components/ReportBanner';
import { ReportNotes } from './components/ReportNotes';
import { useDashboard } from './hooks/useDashboard';

export function App() {
  const { data, loading, error, connected, filters, setFilters, search, setSearch, selectReport, addNote, updateReportStatus, updateReportSeverity, riskPoles, riskSummary } = useDashboard();

  const selectedReportId = data?.selectedReport?.id ?? null;
  const selectedPoleId = data?.selectedPole?.id ?? null;

  function handleSelectPole(poleId: string) {
    const report = data?.reports.find((r) => r.poleId === poleId);
    if (report) selectReport(report.id);
  }

  if (loading) {
    return (
      <div className="wrap" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200 }}>
        <span className="muted">Loading dashboard…</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="wrap">
        <div className="error-banner">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          {error ?? 'Unknown error'}
        </div>
      </div>
    );
  }

  return (
    <div className="wrap">
      {/* Live indicator */}
      <div
        style={{
          position: 'fixed',
          top: 12,
          right: 12,
          zIndex: 50,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          background: 'var(--card)',
          border: '1px solid var(--border)',
          borderRadius: 999,
          padding: '4px 10px',
          fontSize: 11,
          color: connected ? '#34D399' : '#94A3B8',
        }}
        aria-live="polite"
        aria-label={connected ? 'Live updates connected' : 'Reconnecting…'}
      >
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: connected ? '#34D399' : '#94A3B8',
            display: 'inline-block',
          }}
        />
        {connected ? 'Live' : 'Reconnecting…'}
      </div>

      <Header
        summary={data.summary}
        currentUser={data.currentUser}
        filterControl={<DashboardFilters options={data.filters} value={filters} onChange={setFilters} />}
        searchControl={<HeaderSearch value={search} onChange={setSearch} />}
      />

      <KpiCards summary={data.summary} />

      {/* Predictive risk summary strip */}
      {riskSummary && riskSummary.scored > 0 && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 14px',
            marginBottom: 10,
            background: 'rgba(167,139,250,0.07)',
            border: '1px solid rgba(167,139,250,0.22)',
            borderRadius: 10,
            fontSize: 12,
            flexWrap: 'wrap',
          }}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, color: '#A78BFA', fontWeight: 600 }}>
            <svg width="12" height="12" viewBox="0 0 10 10" fill="none">
              <circle cx="5" cy="5" r="4" stroke="#A78BFA" strokeWidth="1.5" strokeDasharray="2 1.5" fill="none" />
            </svg>
            Predicted risk
          </span>
          <span style={{ color: 'var(--muted)' }}>{riskSummary.scored.toLocaleString()} poles scored</span>
          {riskSummary.avgScore !== null && (
            <span style={{ color: 'var(--muted)' }}>avg {riskSummary.avgScore.toFixed(0)}/100</span>
          )}
          <span style={{ color: 'var(--muted)', marginLeft: 2 }}>·</span>
          {riskSummary.critical > 0 && (
            <span style={{ color: '#EF4444' }}>{riskSummary.critical} critical</span>
          )}
          {riskSummary.high > 0 && (
            <span style={{ color: '#F97316' }}>{riskSummary.high} high</span>
          )}
          {riskSummary.medium > 0 && (
            <span style={{ color: '#FBBF24' }}>{riskSummary.medium} medium</span>
          )}
          {riskSummary.low > 0 && (
            <span style={{ color: '#10B981' }}>{riskSummary.low} low</span>
          )}
          {riskSummary.unscored > 0 && (
            <span style={{ color: 'var(--muted)', marginLeft: 'auto' }}>{riskSummary.unscored.toLocaleString()} unscored · run compute_risk CLI to score</span>
          )}
        </div>
      )}

      {/* Map + report list */}
      <div className="dashboard-main" style={{ marginBottom: 14 }}>
        <GridMap
          poles={data.mapPoles}
          totalPoleCount={data.mapPoleCount}
          selectedPoleId={selectedPoleId}
          onSelectPole={handleSelectPole}
          riskPoles={riskPoles}
        />
        <IncomingReports
          reports={data.reports}
          selectedReportId={selectedReportId}
          onSelectReport={selectReport}
        />
      </div>

      {/* Selected report banner */}
      {data.selectedReport && (
        <ReportBanner
          report={data.selectedReport}
          onSeverityChange={(severity) => updateReportSeverity(data.selectedReport!.id, severity)}
          onDismiss={(note) => updateReportStatus(data.selectedReport!.id, 'dismissed', note)}
          onApprove={(note) => updateReportStatus(data.selectedReport!.id, 'approved', note)}
        />
      )}

      {/* Pole detail + photos */}
      {(data.selectedPole || data.photos.length > 0) && (
        <div className="two-col-equal" style={{ marginBottom: 14 }}>
          {data.selectedPole && <PoleDetails pole={data.selectedPole} />}
          {data.photos.length > 0 && (
            <FieldPhotos
              photos={data.photos}
              inspectorLabel="Inspector 2031 · DJI Mavic 3T"
            />
          )}
        </div>
      )}

      {/* Notes */}
      {data.selectedReport && (
        <ReportNotes
          reportId={data.selectedReport.id}
          noteCount={data.noteCount}
          currentUser={data.currentUser}
          onAddNote={addNote}
        />
      )}

      {/* History */}
      {data.history && <PoleHistory history={data.history} />}
    </div>
  );
}
