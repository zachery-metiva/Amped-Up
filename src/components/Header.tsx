import { DashboardSummary, User } from '../types';

interface HeaderProps {
  summary: DashboardSummary;
  currentUser: User;
}

export function Header({ summary, currentUser }: HeaderProps) {
  const displayDate = new Date(summary.date).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div className="row" style={{ marginBottom: 18 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div className="logo-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="#FBBF24" />
          </svg>
        </div>
        <div>
          <div className="header-title">Amped Up</div>
          <div className="muted" style={{ marginTop: 3 }}>
            Grid sector {summary.sector} · {summary.totalPoles} poles tracked · {summary.openReports} open reports · {displayDate}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <button className="btn" aria-label="Filter">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
          </svg>
          Filter
        </button>
        <button className="btn" aria-label="Search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          </svg>
          Search
        </button>
        <button className="btn icon-btn" aria-label="Notifications">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
        </button>
        <div
          className="avatar"
          style={{ width: 30, height: 30, fontSize: 11, background: '#1E40AF', color: '#DBEAFE' }}
          title={currentUser.name}
        >
          {currentUser.initials}
        </div>
      </div>
    </div>
  );
}
