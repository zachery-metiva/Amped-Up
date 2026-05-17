import { ReactNode } from 'react';
import { DashboardSummary, User } from '../types';

interface HeaderProps {
  summary: DashboardSummary;
  currentUser: User;
  filterControl?: ReactNode;
  searchControl?: ReactNode;
}

export function Header({ summary, currentUser, filterControl, searchControl }: HeaderProps) {
  const displayDate = new Date(summary.date).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div className="row app-header">
      <div className="app-header-brand">
        <a
          href="/login"
          className="app-header-logo-link"
          aria-label="Go to login"
        >
          <div className="logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="#FBBF24" />
            </svg>
          </div>
          <div className="header-title">Amped Up</div>
        </a>
        <div className="muted app-header-meta">
          Grid sector {summary.sector} · {summary.totalPoles} poles tracked · {summary.openReports} open reports · {displayDate}
        </div>
      </div>

      <div className="app-header-actions">
        {filterControl}
        {searchControl}
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
