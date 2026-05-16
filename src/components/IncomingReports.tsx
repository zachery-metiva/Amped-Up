import { Report, Severity } from '../types';

const SEVERITY_COLOR: Record<Severity, string> = {
  critical: 'var(--crit)',
  high: 'var(--high)',
  medium: 'var(--med)',
  low: 'var(--low)',
};

const SEVERITY_PILL: Record<Severity, { bg: string; color: string; label: string }> = {
  critical: { bg: 'var(--crit-bg)', color: 'var(--crit-tx)', label: 'Critical' },
  high: { bg: 'var(--high-bg)', color: 'var(--high-tx)', label: 'High' },
  medium: { bg: 'var(--med-bg)', color: 'var(--med-tx)', label: 'Medium' },
  low: { bg: '#064E3B', color: '#A7F3D0', label: 'Low' },
};

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

interface IncomingReportsProps {
  reports: Report[];
  selectedReportId: string | null;
  onSelectReport: (id: string) => void;
}

export function IncomingReports({ reports, selectedReportId, onSelectReport }: IncomingReportsProps) {
  return (
    <div className="card" style={{ padding: 14 }}>
      <div className="row" style={{ marginBottom: 12 }}>
        <h4>Incoming reports · {reports.length} open</h4>
        <span style={{ fontSize: 11.5, color: '#60A5FA', cursor: 'pointer' }}>
          View all{' '}
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" style={{ verticalAlign: 'middle' }}>
            <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
          </svg>
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {reports.map((report) => {
          const p = SEVERITY_PILL[report.severity];
          const isSelected = report.id === selectedReportId;
          return (
            <button
              key={report.id}
              className={`issue${isSelected ? ' sel' : ''}`}
              onClick={() => onSelectReport(report.id)}
              aria-pressed={isSelected}
            >
              <span className="dot" style={{ background: SEVERITY_COLOR[report.severity] }} />
              <div style={{ flex: 1, minWidth: 0, textAlign: 'left' }}>
                <div style={{ fontSize: 12.5, color: 'var(--primary)', fontWeight: 500 }}>
                  {report.poleId} · {report.title}
                </div>
                <div className="muted" style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 3 }}>
                  <div className="avatar" style={{ width: 16, height: 16, fontSize: 8 }}>
                    {report.submittedBy.initials}
                  </div>
                  <span>
                    {report.id} · {report.submittedBy.name} · {timeAgo(report.submittedAt)} · {report.location}
                  </span>
                </div>
              </div>
              <span className="pill" style={{ background: p.bg, color: p.color }}>
                {p.label}
              </span>
            </button>
          );
        })}

        {reports.length === 0 && (
          <div className="muted" style={{ textAlign: 'center', padding: '20px 0' }}>No open reports</div>
        )}
      </div>
    </div>
  );
}
