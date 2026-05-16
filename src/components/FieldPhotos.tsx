import { FieldPhoto, Severity } from '../types';

const SEV_STYLE: Record<Severity, { bg: string; color: string }> = {
  critical: { bg: 'var(--crit-bg)', color: 'var(--crit-tx)' },
  high: { bg: 'var(--high-bg)', color: 'var(--high-tx)' },
  medium: { bg: 'var(--med-bg)', color: 'var(--med-tx)' },
  low: { bg: '#064E3B', color: '#A7F3D0' },
};

// SVG placeholder illustrations — in production replace with <img> and signed URLs
function PhotoPlaceholder({ index }: { index: number }) {
  if (index === 0) {
    return (
      <svg viewBox="0 0 120 90" style={{ width: '100%', height: '100%' }}>
        <rect width="120" height="90" fill="#1E293B" />
        <rect x="0" y="60" width="120" height="30" fill="#0F172A" />
        <circle cx="92" cy="22" r="10" fill="#FBBF24" opacity="0.35" />
        <g transform="translate(48,8) rotate(12)">
          <rect x="-2" y="0" width="4" height="62" fill="#78350F" />
          <rect x="-14" y="14" width="28" height="3" fill="#451A03" />
          <circle cx="-10" cy="16" r="2" fill="#1F2937" />
          <circle cx="10" cy="16" r="2" fill="#1F2937" />
          <rect x="-8" y="22" width="16" height="6" fill="#374151" />
        </g>
      </svg>
    );
  }
  if (index === 1) {
    return (
      <svg viewBox="0 0 120 90" style={{ width: '100%', height: '100%' }}>
        <rect width="120" height="90" fill="#0F172A" />
        <g transform="translate(60,10)">
          <rect x="-3" y="0" width="6" height="80" fill="#6B4423" />
          <rect x="-22" y="10" width="44" height="5" fill="#3F2917" />
          <circle cx="-16" cy="12.5" r="2.5" fill="#1F2937" />
          <circle cx="0" cy="12.5" r="2.5" fill="#1F2937" />
          <circle cx="16" cy="12.5" r="2.5" fill="#1F2937" />
          <path d="M-4,20 L-8,40 L-2,45 L2,45 L8,40 L4,20 Z" fill="#451A03" opacity="0.85" />
        </g>
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 120 90" style={{ width: '100%', height: '100%' }}>
      <rect width="120" height="90" fill="#1E293B" />
      <g transform="translate(60,8)">
        <rect x="-3" y="0" width="6" height="80" fill="#78350F" />
        <rect x="-20" y="20" width="40" height="4" fill="#451A03" />
        <rect x="-3" y="48" width="6" height="22" fill="#374151" />
        <circle cx="0" cy="58" r="6" fill="#1F2937" />
      </g>
      <circle cx="60" cy="65" r="2" fill="#0F172A" opacity="0.6" />
    </svg>
  );
}

interface FieldPhotosProps {
  photos: FieldPhoto[];
  inspectorLabel?: string;
}

export function FieldPhotos({ photos, inspectorLabel }: FieldPhotosProps) {
  return (
    <div className="card" style={{ padding: 14 }}>
      <div className="row" style={{ marginBottom: 12 }}>
        <h4>Field photos · {photos.length} submitted</h4>
        {inspectorLabel && (
          <span className="muted">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" style={{ verticalAlign: 'middle' }}>
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>{' '}
            {inspectorLabel}
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.max(photos.length, 1)}, 1fr)`, gap: 8 }}>
        {photos.map((photo, i) => {
          const sevStyle = photo.severity ? SEV_STYLE[photo.severity] : null;
          return (
            <div key={photo.id} className="photo-frame">
              <PhotoPlaceholder index={i} />
              <span className="photo-label">{photo.label}</span>
              {photo.severityLabel && sevStyle && (
                <span className="photo-sev" style={{ background: sevStyle.bg, color: sevStyle.color }}>
                  {photo.severityLabel}
                </span>
              )}
            </div>
          );
        })}

        {photos.length === 0 && (
          <div className="muted" style={{ gridColumn: '1/-1', textAlign: 'center', padding: '20px 0' }}>
            No photos submitted
          </div>
        )}
      </div>
    </div>
  );
}
