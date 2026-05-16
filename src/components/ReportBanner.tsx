import { SelectedReport } from '../types';

interface ReportBannerProps {
  report: SelectedReport;
  onSnooze: () => void;
  onDismiss: () => void;
  onApprove: () => void;
}

export function ReportBanner({ report, onSnooze, onDismiss, onApprove }: ReportBannerProps) {
  const submittedDate = new Date(report.submittedAt).toLocaleString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });

  return (
    <div className="card report-banner" style={{ padding: 14, marginBottom: 14 }}>
      <div className="row" style={{ flexWrap: 'wrap', gap: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 0 }}>
          <span className="pill" style={{ background: '#1E3A5F', color: '#93C5FD', fontSize: 11.5, padding: '5px 10px', whiteSpace: 'nowrap' }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" style={{ verticalAlign: 'middle' }}>
              <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" /><line x1="4" y1="22" x2="4" y2="15" />
            </svg>{' '}
            Report {report.id}
          </span>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--primary)' }}>
              {report.poleId} · {report.title}
            </div>
            <div className="muted" style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 3 }}>
              <div className="avatar" style={{ width: 18, height: 18, fontSize: 9 }}>
                {report.submittedBy.initials}
              </div>
              <span>
                Submitted by {report.submittedBy.name} · {report.submittedBy.role} ID {report.submittedBy.id} · {submittedDate}
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn" onClick={onSnooze}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
            </svg>
            Snooze
          </button>
          <button className="btn btn-dng" onClick={onDismiss}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
            Dismiss report
          </button>
          <button className="btn btn-pri" onClick={onApprove}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            Approve report
          </button>
        </div>
      </div>
    </div>
  );
}
