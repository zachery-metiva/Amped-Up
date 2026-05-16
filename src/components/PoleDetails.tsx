import { CSSProperties } from 'react';
import { PoleDetail, Severity } from '../types';

const SEVERITY_PILL: Record<Severity, { bg: string; color: string; dot: string; label: string }> = {
  critical: { bg: 'var(--crit-bg)', color: 'var(--crit-tx)', dot: 'var(--crit)', label: 'Critical' },
  high: { bg: 'var(--high-bg)', color: 'var(--high-tx)', dot: 'var(--high)', label: 'High' },
  medium: { bg: 'var(--med-bg)', color: 'var(--med-tx)', dot: 'var(--med)', label: 'Medium' },
  low: { bg: '#064E3B', color: '#A7F3D0', dot: 'var(--low)', label: 'Low' },
};

interface PoleDetailsProps {
  pole: PoleDetail;
}

interface MetaRowProps {
  label: string;
  value: string;
  valueStyle?: CSSProperties;
}

function MetaRow({ label, value, valueStyle }: MetaRowProps) {
  return (
    <>
      <span className="meta-key">{label}</span>
      <span style={valueStyle}>{value}</span>
    </>
  );
}

export function PoleDetails({ pole }: PoleDetailsProps) {
  const p = SEVERITY_PILL[pole.severity];

  return (
    <div className="card" style={{ padding: 14 }}>
      <div className="row" style={{ marginBottom: 12 }}>
        <div>
          <h4 style={{ marginBottom: 6 }}>Selected pole</h4>
          <div style={{ fontSize: 15, fontWeight: 500, color: 'var(--primary)' }}>
            {pole.id} · {pole.classification}
          </div>
          <div className="muted" style={{ marginTop: 3 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" style={{ verticalAlign: 'middle' }}>
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
            </svg>{' '}
            {pole.address} · {pole.lat.toFixed(4)}° N, {Math.abs(pole.lon).toFixed(4)}° W
          </div>
        </div>
        <span className="pill" style={{ background: p.bg, color: p.color }}>
          <span className="dot" style={{ background: p.dot }} />
          {p.label}
        </span>
      </div>

      <div className="meta-grid" style={{ paddingTop: 10, borderTop: '1px solid var(--border)' }}>
        <MetaRow label="Height" value={pole.height} />
        <MetaRow label="Owner" value={pole.owner} />
        <MetaRow label="Circuit" value={pole.circuit} />
        <MetaRow
          label="Lean"
          value={pole.lean ?? 'Within spec'}
          valueStyle={pole.lean ? { color: 'var(--crit-tx)' } : undefined}
        />
        <MetaRow
          label="AI score"
          value={`${pole.aiScore} · ${pole.aiConfidence}`}
          valueStyle={pole.severity === 'critical' || pole.severity === 'high' ? { color: 'var(--crit-tx)' } : undefined}
        />
        <MetaRow label="Recommended" value={pole.recommendation} />
      </div>
    </div>
  );
}
