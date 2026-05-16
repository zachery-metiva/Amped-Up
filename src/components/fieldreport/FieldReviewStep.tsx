import { useEffect, useState } from 'react';
import { CapturedPhoto, GpsCoords } from '../../types/submission';

type SeverityLevel = 'critical' | 'high' | 'medium' | 'low';

interface AiFinding {
  severity: SeverityLevel;
  finding: string;
  confidence: number;
  nesc: string;
  action: string;
}

// Deterministic pool — picked by photo count so the finding is consistent per session
const AI_FINDINGS: AiFinding[] = [
  { severity: 'critical', finding: '12° lean detected — pole has exceeded NESC structural tolerance. Risk of collapse under load.', confidence: 94, nesc: 'NESC 261', action: 'Immediate isolation and emergency repair order required' },
  { severity: 'high',     finding: 'Insulator tracking marks visible on upper crossarm — elevated flashover risk under wet conditions.', confidence: 82, nesc: 'NESC 277', action: 'Schedule insulator replacement within 30 days' },
  { severity: 'critical', finding: 'Active conductor contact with vegetation confirmed in overview photo — immediate clearance violation.', confidence: 88, nesc: 'NESC 218', action: 'De-energize circuit and clear vegetation before re-energizing' },
  { severity: 'high',     finding: 'Transformer oil staining on pole body — dielectric contamination risk.', confidence: 85, nesc: 'OSHA 1910.269', action: 'Test transformer dielectric; replace unit if below spec' },
  { severity: 'medium',   finding: 'Woodpecker damage detected in upper third of pole — structural integrity may be compromised.', confidence: 71, nesc: 'ANSI O5.1', action: 'Bore and probe test required; treat if sound wood is below spec' },
  { severity: 'critical', finding: 'Crossarm rot and decay — load-bearing failure risk identified in damage photo.', confidence: 91, nesc: 'NESC 261', action: 'Out-of-service order; do not climb without shoring support' },
  { severity: 'high',     finding: 'Guy wire corrosion at anchor plate — tensile strength may be significantly reduced.', confidence: 79, nesc: 'NESC 261', action: 'Guy wire replacement required; temporary guy recommended immediately' },
  { severity: 'medium',   finding: 'Vegetation within 3 ft of conductor clearance zone — approaching NESC minimum.', confidence: 76, nesc: 'NESC 218', action: 'Schedule trim within 60 days per cycle plan' },
  { severity: 'low',      finding: 'Surface weathering and UV chalk noted — pole within compliance but showing age indicators.', confidence: 67, nesc: 'ANSI O5.1', action: 'Note for next scheduled inspection cycle' },
  { severity: 'medium',   finding: 'Faded pole ID markings — compliance gap with MPSC inspection requirements.', confidence: 88, nesc: 'MPSC R 460.601', action: 'Re-stencil or re-tag within 90 days' },
];

const SEV: Record<SeverityLevel, { label: string; color: string; bg: string; border: string }> = {
  critical: { label: 'Critical', color: '#FECACA', bg: '#3F0808', border: '#EF4444' },
  high:     { label: 'High',     color: '#FED7AA', bg: '#431407', border: '#F97316' },
  medium:   { label: 'Medium',   color: '#FDE68A', bg: '#451A03', border: '#FBBF24' },
  low:      { label: 'Low',      color: '#BBF7D0', bg: '#052E16', border: '#22C55E' },
};

const POLE_TYPES = [
  { id: '', label: 'Unknown / not specified' },
  { id: 'sp35c5', label: 'SP 35 ft Cls 5 — Single-phase rural' },
  { id: 'ju40c4', label: 'JU 40 ft Cls 4 — Joint-use urban' },
  { id: 'de45c3', label: 'DE 45 ft Cls 3 — Dead-end' },
  { id: 'daw46',  label: 'DAW 46 kV — Sub-transmission wood' },
  { id: 'serv30c6', label: 'Serv 30 ft Cls 6 — Service pole' },
  { id: 'ang40c4', label: 'ANG 40 ft Cls 4 — Angle pole' },
  { id: 'hfw69',  label: 'HFW 69 kV — H-frame wood' },
  { id: 'tap40c4', label: 'TAP 40 ft Cls 4 — Tap pole' },
  { id: 'hfs138', label: 'HFS 138 kV — H-frame steel' },
  { id: 'tds115', label: 'TDS 115 kV — Transmission dead-end steel' },
  { id: 'bank45c3', label: 'Bank 45 ft Cls 3 — Transformer bank' },
  { id: 'riser40c4', label: 'Riser 40 ft Cls 4 — Underground riser' },
  { id: 'other', label: 'Other' },
];

interface FieldReviewStepProps {
  poleId: string;
  photos: CapturedPhoto[];
  location: GpsCoords | null;
  onBack: () => void;
  onSubmit: (payload: FieldReportPayload) => Promise<void>;
}

export interface FieldReportPayload {
  pole_id: string;
  pole_type: string | null;
  classification: string | null;
  owner: string | null;
  circuit: string | null;
  address: string | null;
  location: { lat: number; lon: number; accuracy: number } | null;
  severity: SeverityLevel;
  description: string;
  photo_count: number;
}

export function FieldReviewStep({ poleId: initialPoleId, photos, location, onBack, onSubmit }: FieldReviewStepProps) {
  // AI analysis state
  const [aiState, setAiState] = useState<'analyzing' | 'done'>('analyzing');
  const [aiFinding, setAiFinding] = useState<AiFinding>(AI_FINDINGS[0]);

  // Editable fields — pre-filled where possible
  const [poleId, setPoleId] = useState(initialPoleId);
  const [poleType, setPoleType] = useState('');
  const [classification, setClassification] = useState('');
  const [owner, setOwner] = useState('');
  const [circuit, setCircuit] = useState('');
  const [address, setAddress] = useState('');
  const [latStr, setLatStr] = useState(location ? location.lat.toFixed(6) : '');
  const [lonStr, setLonStr] = useState(location ? location.lon.toFixed(6) : '');
  const [severity, setSeverity] = useState<SeverityLevel>('medium');
  const [description, setDescription] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Simulate AI analyzing the photos when this step mounts
  useEffect(() => {
    const finding = AI_FINDINGS[photos.length % AI_FINDINGS.length];
    const timer = setTimeout(() => {
      setAiFinding(finding);
      setSeverity(finding.severity);
      setAiState('done');
    }, 1800);
    return () => clearTimeout(timer);
  }, [photos.length]);

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({
        pole_id: poleId.trim() || initialPoleId,
        pole_type: poleType || null,
        classification: classification || null,
        owner: owner || null,
        circuit: circuit || null,
        address: address || null,
        location: latStr && lonStr
          ? { lat: parseFloat(latStr), lon: parseFloat(lonStr), accuracy: location?.accuracy ?? 0 }
          : null,
        severity,
        description,
        photo_count: photos.length,
      });
    } catch {
      setError('Submission failed. Check your connection and try again.');
      setSubmitting(false);
    }
  }

  return (
    <div className="sub-screen">
      {/* Header */}
      <div className="sub-hdr">
        <button className="sub-ico-btn" onClick={onBack} aria-label="Back">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
          </svg>
        </button>
        <div className="sub-hdr-title">
          <span>Field report</span>
          <span className="sub-hdr-sub">Step 2 of 2 · Review &amp; submit</span>
        </div>
        <div style={{ width: 32 }} />
      </div>

      <div className="sub-review-body">

        {/* Photos */}
        <section className="sub-section">
          <h3 className="sub-section-label">Photos ({photos.length})</h3>
          <div className="sub-review-photos">
            {photos.map((p) => (
              <div key={p.id} className="sub-review-photo">
                <img src={p.dataUrl} alt={p.label} />
                <span className="sub-review-photo-lbl">{p.label}</span>
              </div>
            ))}
          </div>
        </section>

        {/* AI recommendation */}
        <section className="fr-ai-panel">
          {aiState === 'analyzing' ? (
            <div className="fr-ai-hdr">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#93C5FD" strokeWidth="2" className="sub-spin">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              Analyzing {photos.length} photo{photos.length !== 1 ? 's' : ''}…
            </div>
          ) : (
            <>
              <div className="fr-ai-hdr">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#93C5FD" strokeWidth="2">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
                AI analysis · {photos.length} photo{photos.length !== 1 ? 's' : ''} reviewed
                <span className="fr-ai-confidence">{aiFinding.confidence}% confidence</span>
              </div>
              <p className="fr-ai-finding">{aiFinding.finding}</p>
              <div className="fr-ai-meta">
                <span className="fr-ai-nesc">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
                  </svg>
                  {aiFinding.nesc}
                </span>
                <span className="fr-ai-action">{aiFinding.action}</span>
              </div>
              <p className="fr-ai-nudge">
                Recommended severity: <strong style={{ color: SEV[aiFinding.severity].color }}>{SEV[aiFinding.severity].label}</strong>. Adjust below if needed.
              </p>
            </>
          )}
        </section>

        {/* Severity */}
        <section className="sub-section">
          <h3 className="sub-section-label">Severity</h3>
          <div className="fr-sev-row">
            {(['critical', 'high', 'medium', 'low'] as SeverityLevel[]).map((s) => {
              const meta = SEV[s];
              const active = severity === s;
              return (
                <button
                  key={s}
                  className={`fr-sev-btn${active ? ' active' : ''}`}
                  style={active ? { borderColor: meta.border, background: meta.bg, color: meta.color } : {}}
                  onClick={() => setSeverity(s)}
                >
                  {meta.label}
                </button>
              );
            })}
          </div>
        </section>

        {/* Pole identity */}
        <section className="sub-section">
          <h3 className="sub-section-label">Pole identity</h3>
          <div className="fr-field-group">
            <label className="fr-label">Pole ID</label>
            <input className="fr-input" value={poleId} onChange={(e) => setPoleId(e.target.value)} placeholder="e.g. P-1147" />
          </div>
          <div className="fr-field-group">
            <label className="fr-label">Pole type</label>
            <select className="fr-select" value={poleType} onChange={(e) => setPoleType(e.target.value)}>
              {POLE_TYPES.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
            </select>
          </div>
          <div className="fr-row">
            <div className="fr-field-group">
              <label className="fr-label">Classification</label>
              <input className="fr-input" value={classification} onChange={(e) => setClassification(e.target.value)} placeholder="e.g. Class 4" />
            </div>
            <div className="fr-field-group">
              <label className="fr-label">Owner</label>
              <input className="fr-input" value={owner} onChange={(e) => setOwner(e.target.value)} placeholder="e.g. DTE Energy" />
            </div>
          </div>
          <div className="fr-field-group">
            <label className="fr-label">Circuit</label>
            <input className="fr-input" value={circuit} onChange={(e) => setCircuit(e.target.value)} placeholder="e.g. CKT-04A" />
          </div>
        </section>

        {/* Location */}
        <section className="sub-section">
          <h3 className="sub-section-label">Location</h3>
          {location && (
            <div className="fr-gps-badge">
              <span className="fr-pulse" />
              GPS captured · ±{location.accuracy.toFixed(1)} m accuracy
            </div>
          )}
          <div className="fr-row">
            <div className="fr-field-group">
              <label className="fr-label">Latitude</label>
              <input className="fr-input fr-mono" value={latStr} onChange={(e) => setLatStr(e.target.value)} placeholder="e.g. 42.331429" />
            </div>
            <div className="fr-field-group">
              <label className="fr-label">Longitude</label>
              <input className="fr-input fr-mono" value={lonStr} onChange={(e) => setLonStr(e.target.value)} placeholder="e.g. -83.045753" />
            </div>
          </div>
          <div className="fr-field-group">
            <label className="fr-label">Address / landmark</label>
            <input className="fr-input" value={address} onChange={(e) => setAddress(e.target.value)} placeholder="e.g. Elm St & 7th Ave" />
          </div>
        </section>

        {/* Description */}
        <section className="sub-section">
          <h3 className="sub-section-label">
            Description <span className="sub-section-opt">(optional)</span>
          </h3>
          <textarea
            className="sub-textarea"
            placeholder="Describe what you observed — damage type, extent, any immediate safety hazard…"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            maxLength={1000}
          />
          <div className="sub-char-count">{description.length} / 1000</div>
        </section>

        {error && <p className="sub-error">{error}</p>}

        <button className="fr-submit-btn" onClick={handleSubmit} disabled={submitting}>
          {submitting ? (
            <>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="sub-spin">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              Submitting…
            </>
          ) : (
            <>
              Submit report
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </>
          )}
        </button>

        <div style={{ height: 24 }} />
      </div>
    </div>
  );
}
