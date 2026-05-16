import { HistoryEvent, PoleHistory as PoleHistoryType } from '../types';

function formatDate(iso: string | null): string {
  if (!iso) return 'Date unknown';
  const d = new Date(iso);
  if (iso.includes('T')) {
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  }
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function TimelineItem({ event }: { event: HistoryEvent }) {
  const isComment = event.type === 'comment';

  return (
    <div className={`tl-item${isComment ? ' tl-comment-item' : ''}`}>
      <span className="tl-pin" style={{ background: event.pinColor }} aria-hidden="true">
        {isComment && (
          <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="#E2E8F0" strokeWidth="2.5" aria-hidden="true">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        )}
      </span>

      <div className="row" style={{ alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: isComment ? 12.5 : 13, color: 'var(--primary)', fontWeight: 500 }}>
          {event.author && <div className="avatar">{event.author.initials}</div>}
          {event.title}
        </div>
        <span className="muted" style={{ whiteSpace: 'nowrap' }}>{formatDate(event.date)}</span>
      </div>

      {event.description && (
        <div className="muted" style={{ marginTop: 2 }}>{event.description}</div>
      )}

      {event.comment && (
        <div className="tl-comment-body">{event.comment}</div>
      )}
    </div>
  );
}

interface PoleHistoryProps {
  history: PoleHistoryType;
}

export function PoleHistory({ history }: PoleHistoryProps) {
  const lifecycleLabel = history.lifecycleYears !== null
    ? `Lifecycle ${history.lifecycleYears} years`
    : 'Install date unknown';

  return (
    <div className="card" style={{ padding: 14 }}>
      <div className="row" style={{ marginBottom: 14 }}>
        <h4>Pole history</h4>
        <span className="muted">
          {lifecycleLabel} · {history.eventCount} events · {history.commentCount} comments
        </span>
      </div>

      <div className="timeline">
        <div className="tl-rail" aria-hidden="true" />
        {history.events.map((event) => (
          <TimelineItem key={event.id} event={event} />
        ))}
      </div>
    </div>
  );
}
