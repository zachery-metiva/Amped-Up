import { DashboardSummary } from '../types';

interface KpiCardsProps {
  summary: DashboardSummary;
}

export function KpiCards({ summary }: KpiCardsProps) {
  return (
    <div className="kpi-grid">
      <div className="card kpi">
        <h4>Total poles</h4>
        <div className="kpi-value">{summary.totalPoles}</div>
        <div className="muted">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#34D399" strokeWidth="2" aria-hidden="true">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" /><polyline points="17 6 23 6 23 12" />
          </svg>{' '}
          {summary.newSinceLastScan} since last scan
        </div>
      </div>

      <div className="card kpi">
        <span className="kpi-dot" style={{ background: 'var(--crit)' }} />
        <h4 style={{ color: 'var(--crit-tx)' }}>Critical</h4>
        <div className="kpi-value">{summary.critical}</div>
        <div className="muted">Immediate action</div>
      </div>

      <div className="card kpi">
        <span className="kpi-dot" style={{ background: 'var(--high)' }} />
        <h4 style={{ color: 'var(--high-tx)' }}>High</h4>
        <div className="kpi-value">{summary.high}</div>
        <div className="muted">Within 30 days</div>
      </div>

      <div className="card kpi">
        <span className="kpi-dot" style={{ background: 'var(--med)' }} />
        <h4 style={{ color: 'var(--med-tx)' }}>Medium</h4>
        <div className="kpi-value">{summary.medium}</div>
        <div className="muted">Within 90 days</div>
      </div>
    </div>
  );
}
