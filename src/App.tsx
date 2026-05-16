import { FieldPhotos } from './components/FieldPhotos';
import { GridMap } from './components/GridMap';
import { Header } from './components/Header';
import { IncomingReports } from './components/IncomingReports';
import { KpiCards } from './components/KpiCards';
import { PoleDetails } from './components/PoleDetails';
import { PoleHistory } from './components/PoleHistory';
import { ReportBanner } from './components/ReportBanner';
import { ReportNotes } from './components/ReportNotes';
import { useDashboard } from './hooks/useDashboard';

export function App() {
  const { data, loading, error, connected, selectReport, addNote, updateReportStatus } = useDashboard();

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

      <Header summary={data.summary} currentUser={data.currentUser} />

      <KpiCards summary={data.summary} />

      {/* Map + report list */}
      <div className="two-col-wide" style={{ marginBottom: 14 }}>
        <GridMap
          poles={data.mapPoles}
          selectedPoleId={selectedPoleId}
          onSelectPole={handleSelectPole}
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
          onSnooze={() => updateReportStatus(data.selectedReport!.id, 'snoozed')}
          onDismiss={() => updateReportStatus(data.selectedReport!.id, 'dismissed')}
          onApprove={() => updateReportStatus(data.selectedReport!.id, 'approved')}
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
