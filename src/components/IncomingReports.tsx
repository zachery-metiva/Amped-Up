import { useState } from 'react';
import { PredictedReport, Report, ReportStatus, Severity } from '../types';

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

const STATUS_LABEL: Record<ReportStatus, string> = {
  open: 'Open',
  snoozed: 'Snoozed',
  approved: 'Approved',
  dismissed: 'Dismissed',
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
  predictedReports: PredictedReport[];
  selectedReportId: string | null;
  selectedPoleId: string | null;
  onSelectReport: (id: string) => void;
  onSelectPole: (poleId: string) => void;
}

function formatComputedAt(iso: string): string {
  if (!iso) return 'not yet timestamped';
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function riskFactorSummary(factors: Record<string, unknown> | null): string {
  if (!factors) return 'No factor details available';
  return Object.entries(factors)
    .filter(([key]) => !key.startsWith('_'))
    .slice(0, 3)
    .map(([key, value]) => {
      const fallbackLabel = key.replace(/_/g, ' ');
      if (typeof value === 'number') return `${fallbackLabel}: ${value.toFixed(1)}`;
      if (value && typeof value === 'object') {
        const factor = value as Record<string, unknown>;
        const label = typeof factor.label === 'string' ? factor.label : fallbackLabel;
        const score = typeof factor.score === 'number' ? ` ${factor.score.toFixed(0)}/100` : '';
        return `${label}${score}`;
      }
      return `${fallbackLabel}: ${String(value)}`;
    })
    .join(' - ') || 'No factor details available';
}

export function IncomingReports({ reports, predictedReports, selectedReportId, selectedPoleId, onSelectReport, onSelectPole }: IncomingReportsProps) {
  const [mode, setMode] = useState<'reported' | 'predicted'>('reported');
  const openCount = reports.filter((report) => report.status === 'open').length;
  const sortedPredictedReports = [...predictedReports].sort((a, b) => b.riskScore - a.riskScore);

  return (
    <div className="card reports-card">
      <div className="reports-head">
        <div>
          <h4>{mode === 'reported' ? `Reports - ${reports.length} total - ${openCount} open` : `Predicted issues - ${sortedPredictedReports.length} open`}</h4>
          <div className="muted reports-head-sub">
            {mode === 'reported' ? 'Field-submitted issues awaiting review.' : 'Risk-ranked poles without a submitted report.'}
          </div>
        </div>
        <div className="issue-switch" role="group" aria-label="Issue list mode">
          <button
            type="button"
            className={mode === 'reported' ? 'active' : ''}
            aria-pressed={mode === 'reported'}
            onClick={() => setMode('reported')}
          >
            Reported
          </button>
          <button
            type="button"
            className={mode === 'predicted' ? 'active' : ''}
            aria-pressed={mode === 'predicted'}
            onClick={() => setMode('predicted')}
          >
            Predicted
          </button>
        </div>
      </div>

      <div className="reports-list">
        {mode === 'reported' && reports.map((report) => {
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
              {report.status !== 'open' && (
                <span className="pill report-status-pill">
                  {STATUS_LABEL[report.status]}
                </span>
              )}
            </button>
          );
        })}

        {mode === 'reported' && reports.length === 0 && (
          <div className="muted" style={{ textAlign: 'center', padding: '20px 0' }}>No reports</div>
        )}

        {mode === 'predicted' && sortedPredictedReports.map((report) => {
          const p = SEVERITY_PILL[report.predictedSeverity];
          const isSelected = report.poleId === selectedPoleId;
          return (
            <button
              key={report.id}
              className={`issue predicted-issue${isSelected ? ' sel' : ''}`}
              onClick={() => onSelectPole(report.poleId)}
              aria-pressed={isSelected}
            >
              <span className="dot" style={{ background: SEVERITY_COLOR[report.predictedSeverity] }} />
              <div style={{ flex: 1, minWidth: 0, textAlign: 'left' }}>
                <div style={{ fontSize: 12.5, color: 'var(--primary)', fontWeight: 500 }}>
                  {report.poleId} - Risk score {report.riskScore.toFixed(0)}
                </div>
                <div className="muted" style={{ marginTop: 3 }}>
                  {riskFactorSummary(report.riskFactors)}
                </div>
                <div className="muted" style={{ marginTop: 3 }}>
                  {report.lat.toFixed(4)} N, {Math.abs(report.lon).toFixed(4)} W - generated {formatComputedAt(report.generatedAt)}
                </div>
              </div>
              <span className="pill" style={{ background: p.bg, color: p.color }}>
                {p.label}
              </span>
            </button>
          );
        })}

        {mode === 'predicted' && sortedPredictedReports.length === 0 && (
          <div className="muted" style={{ textAlign: 'center', padding: '20px 0' }}>No predicted issues</div>
        )}
      </div>
    </div>
  );
}

