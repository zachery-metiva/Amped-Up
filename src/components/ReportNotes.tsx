import { useState, KeyboardEvent } from 'react';
import { User } from '../types';

const MAX_LENGTH = 200;

interface ReportNotesProps {
  reportId: string;
  noteCount: number;
  currentUser: User;
  onAddNote: (reportId: string, content: string) => Promise<void>;
}

export function ReportNotes({ reportId, noteCount, currentUser, onAddNote }: ReportNotesProps) {
  const [text, setText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const remaining = MAX_LENGTH - text.length;
  const countColor = remaining <= 20 ? '#FCA5A5' : remaining <= 60 ? '#FCD34D' : 'var(--text-3)';

  async function handleSubmit() {
    const trimmed = text.trim();
    if (!trimmed || submitting) return;
    setSubmitting(true);
    try {
      await onAddNote(reportId, trimmed);
      setText('');
    } finally {
      setSubmitting(false);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div className="card" style={{ padding: 14, marginBottom: 14 }}>
      <div className="row" style={{ marginBottom: 10 }}>
        <div>
          <h4>Report notes</h4>
          <div className="muted" style={{ marginTop: 3 }}>
            Visible to all reviewers. Saved notes appear in the pole history below.
          </div>
        </div>
        <span className="muted" style={{ fontSize: 11 }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" style={{ verticalAlign: 'middle' }}>
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>{' '}
          {noteCount} {noteCount === 1 ? 'note' : 'notes'} on this report
        </span>
      </div>

      <textarea
        className="note-input"
        value={text}
        onChange={(e) => setText(e.target.value.slice(0, MAX_LENGTH))}
        onKeyDown={handleKeyDown}
        maxLength={MAX_LENGTH}
        placeholder="Add a note for the next reviewer. For example: dispatched crew, ETA Friday morning. Max 200 characters."
        rows={3}
        aria-label="Note text"
      />

      <div className="row" style={{ marginTop: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-2)', fontSize: 11.5 }}>
          <div className="avatar">{currentUser.initials}</div>
          <span>Posting as {currentUser.name} · {currentUser.role}</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span className="muted" style={{ fontSize: 11 }}>
            <span style={{ color: countColor }}>{text.length}</span> / {MAX_LENGTH}
          </span>
          <button className="btn" onClick={() => setText('')} disabled={!text}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
            Clear
          </button>
          <button
            className="btn btn-pri"
            onClick={handleSubmit}
            disabled={!text.trim() || submitting}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
            {submitting ? 'Sending…' : 'Add note'}
          </button>
        </div>
      </div>
    </div>
  );
}
