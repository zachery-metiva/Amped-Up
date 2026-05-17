import { useState } from 'react';
import { SelectedReport, Severity } from '../types';

interface ReportBannerProps {
  report: SelectedReport;
  onSeverityChange: (severity: Severity) => void;
  onDismiss: (note?: string) => void;
  onApprove: (note?: string) => void;
}

type ConfirmMode = 'approve' | 'dismiss' | null;

export function ReportBanner({ report, onSeverityChange, onDismiss, onApprove }: ReportBannerProps) {
  const [confirmMode, setConfirmMode] = useState<ConfirmMode>(null);
  const [note, setNote] = useState('');

  const submittedDate = new Date(report.submittedAt).toLocaleString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });

  function handleConfirm() {
    const trimmed = note.trim() || undefined;
    if (confirmMode === 'approve') onApprove(trimmed);
    else if (confirmMode === 'dismiss') onDismiss(trimmed);
    setConfirmMode(null);
    setNote('');
  }

  function handleCancel() {
    setConfirmMode(null);
    setNote('');
  }

  const isApproving = confirmMode === 'approve';

  return (
    <div className="card report-banner" style={{ padding: 14, marginBottom: 14 }}>
      {/* ── Report info row ── */}
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

        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <label className="severity-select-wrap">
            <span>Severity</span>
            <select
              value={report.severity}
              onChange={(event) => onSeverityChange(event.target.value as Severity)}
              aria-label="Change report severity"
              disabled={confirmMode !== null}
            >
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </label>

          {confirmMode === null ? (
            <>
              <button className="btn btn-dng" onClick={() => setConfirmMode('dismiss')}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
                Dismiss
              </button>
              <button className="btn btn-pri" onClick={() => setConfirmMode('approve')}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                Approve
              </button>
            </>
          ) : (
            <>
              <button className="btn" onClick={handleCancel} style={{ color: 'var(--muted)' }}>
                Cancel
              </button>
              <button
                className={`btn ${isApproving ? 'btn-pri' : 'btn-dng'}`}
                onClick={handleConfirm}
              >
                {isApproving ? (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    Confirm approval
                  </>
                ) : (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                    Confirm dismissal
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>

      {/* ── Inline note field shown during confirm step ── */}
      {confirmMode !== null && (
        <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <label style={{ fontSize: 12, color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            {isApproving ? 'Approval note' : 'Dismissal reason'}{' '}
            <span style={{ opacity: 0.55 }}>(optional — saved to report history)</span>
          </label>
          <textarea
            autoFocus
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder={
              isApproving
                ? 'e.g. Confirmed by field inspection on May 17 — work order WO-2031 created…'
                : 'e.g. Duplicate of report RPT-008 — no action required…'
            }
            rows={2}
            maxLength={200}
            style={{
              width: '100%',
              background: 'var(--input-bg, #0F172A)',
              border: `1px solid ${isApproving ? 'rgba(34,197,94,0.35)' : 'rgba(239,68,68,0.35)'}`,
              borderRadius: 8,
              color: 'var(--primary)',
              fontSize: 13,
              padding: '8px 10px',
              resize: 'none',
              outline: 'none',
              fontFamily: 'inherit',
              boxSizing: 'border-box',
            }}
          />
          <div style={{ fontSize: 11, color: 'var(--muted)', textAlign: 'right' }}>{note.length} / 200</div>
        </div>
      )}
    </div>
  );
}
