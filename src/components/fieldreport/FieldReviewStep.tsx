import { useEffect, useRef, useState } from 'react';
import { API_BASE_URL } from '../../config/api';
import { CapturedPhoto, GpsCoords } from '../../types/submission';

type SeverityLevel = 'critical' | 'high' | 'medium' | 'low';

interface AiFinding {
  severity: SeverityLevel;
  finding: string;
  confidence: number;
  nesc: string;
  action: string;
  violation_type_id?: string | null;
  violation_code?: string | null;
  violation_family?: string | null;
  dashboard_title?: string | null;
  regulations?: string[];
  evidence_required?: string | null;
  specifications?: Record<string, string | number | null>;
}

const FALLBACK_FINDING: AiFinding = {
  severity: 'medium',
  finding: 'Submitted photos need reviewer confirmation.',
  confidence: 40,
  nesc: 'NESC field review',
  action: 'Review uploaded images and assign a work priority.',
  dashboard_title: 'Manual photo review',
  regulations: ['NESC field review'],
  evidence_required: 'Review uploaded images, pole context, location, and field notes.',
  specifications: { measurement_kind: 'manual_review' },
};

const SEV: Record<SeverityLevel, { label: string; color: string; bg: string; border: string }> = {
  critical: { label: 'Critical', color: '#FECACA', bg: '#3F0808', border: '#EF4444' },
  high: { label: 'High', color: '#FED7AA', bg: '#431407', border: '#F97316' },
  medium: { label: 'Medium', color: '#FDE68A', bg: '#451A03', border: '#FBBF24' },
  low: { label: 'Low', color: '#BBF7D0', bg: '#052E16', border: '#22C55E' },
};

const SEV_ORDER: SeverityLevel[] = ['low', 'medium', 'high', 'critical'];

const VIOLATION_TAGS: Record<string, string> = {
  transformer_oil_leak: 'Oil leak',
  recloser_oil_leak: 'Oil leak',
  crossarm_split: 'Crossarm split',
  crossarm_decay: 'Crossarm decay',
  pole_lean_excessive: 'Lean',
  stub_lean_excessive: 'Lean',
  groundline_decay: 'Decay',
  pole_decay_groundline: 'Decay',
  pole_decay_woodpecker: 'Decay',
  vegetation_contact_primary: 'Veg. contact',
  vegetation_contact_phase_a: 'Veg. contact',
  vegetation_contact_transmission: 'Veg. contact',
  vegetation_encroachment_primary: 'Veg. encroach.',
  tall_vegetation_in_row: 'Tall vegetation',
  guy_strand_corroded: 'Guy corrosion',
  guy_strand_corrosion: 'Guy corrosion',
  anchor_pulled: 'Anchor pulled',
  anchor_rod_exposed: 'Anchor exposed',
  insulator_arc_tracking: 'Arc tracking',
  polymer_insulator_tracking: 'Arc tracking',
  insulator_string_shattered: 'Shattered insulator',
  conductor_strand_break: 'Strand break',
  open_neutral: 'Open neutral',
  downed_conductor_dead_end_failure: 'Downed conductor',
  dead_end_clamp_failure_phase_c: 'Clamp failure',
  dead_end_clamp_slipped: 'Clamp slipped',
  loose_transformer_hardware: 'Loose hardware',
  loose_bank_hardware: 'Loose hardware',
  loose_tap_clamp: 'Loose clamp',
  splice_thermal_damage: 'Thermal damage',
  riser_insulation_burned: 'Burned insulation',
  missing_equipment_ground: 'Missing ground',
  ground_lead_disconnected: 'Ground disconnect',
  cracked_bushing: 'Cracked bushing',
  jumper_damaged: 'Damaged jumper',
  unauthorized_attachment: 'Unauth. attachment',
  unauthorized_antenna_attachment: 'Unauth. antenna',
  id_tag_missing: 'Missing ID tag',
  id_tag_illegible: 'Faded ID tag',
  pole_id_faded: 'Faded ID tag',
  graffiti: 'Graffiti',
  none: 'No issues',
};

function violationToTag(violations: string[]): string {
  const first = violations.find((v) => v !== 'unknown') ?? 'none';
  if (first in VIOLATION_TAGS) return VIOLATION_TAGS[first];
  return first.split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function worstSeverity(analyses: PhotoAnalysis[]): SeverityLevel {
  return analyses.reduce<SeverityLevel>((worst, analysis) => (
    SEV_ORDER.indexOf(analysis.severity) > SEV_ORDER.indexOf(worst) ? analysis.severity : worst
  ), 'low');
}

interface PhotoAnalysis {
  photoId: string;
  photoLabel: string;
  tag: string;
  severity: SeverityLevel;
  violations: string[];
  oshaClass: string;
  recommendation: string;
  nesc: string[];
  confidence: number;
  poweredBy: string;
  analyzing: boolean;
  failed: boolean;
}

interface SynthesisResult {
  severity: SeverityLevel;
  violations: string[];
  summary: string;
  recommendation: string;
  nesc: string[];
  confidence: number;
  poweredBy: string;
}

const POLE_TYPES = [
  { id: '', label: 'Unknown / not specified' },
  { id: 'sp35c5', label: 'SP 35 ft Cls 5 - Single-phase rural' },
  { id: 'ju40c4', label: 'JU 40 ft Cls 4 - Joint-use urban' },
  { id: 'de45c3', label: 'DE 45 ft Cls 3 - Dead-end' },
  { id: 'daw46', label: 'DAW 46 kV - Sub-transmission wood' },
  { id: 'serv30c6', label: 'Serv 30 ft Cls 6 - Service pole' },
  { id: 'ang40c4', label: 'ANG 40 ft Cls 4 - Angle pole' },
  { id: 'hfw69', label: 'HFW 69 kV - H-frame wood' },
  { id: 'tap40c4', label: 'TAP 40 ft Cls 4 - Tap pole' },
  { id: 'hfs138', label: 'HFS 138 kV - H-frame steel' },
  { id: 'tds115', label: 'TDS 115 kV - Transmission dead-end steel' },
  { id: 'bank45c3', label: 'Bank 45 ft Cls 3 - Transformer bank' },
  { id: 'riser40c4', label: 'Riser 40 ft Cls 4 - Underground riser' },
  { id: 'other', label: 'Other' },
];

interface FieldReviewStepProps {
  poleId: string;
  poleMetadata?: PoleMetadata | null;
  photos: CapturedPhoto[];
  location: GpsCoords | null;
  onPhotoReplace: (index: number, photo: CapturedPhoto) => void;
  onBack: () => void;
  onSubmit: (payload: FieldReportPayload) => Promise<void>;
}

export interface PoleMetadata {
  classification?: string;
  owner?: string;
  circuit?: string;
  address?: string;
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
  photos: Array<{ id: string; label: string; data_url: string }>;
  ai_analysis: AiFinding;
}

export function FieldReviewStep({ poleId: initialPoleId, poleMetadata, photos, location, onPhotoReplace, onBack, onSubmit }: FieldReviewStepProps) {
  const replaceInputRef = useRef<HTMLInputElement>(null);
  const [replacingPhotoIndex, setReplacingPhotoIndex] = useState<number | null>(null);
  const [photoAnalyses, setPhotoAnalyses] = useState<PhotoAnalysis[]>([]);
  const [aiState, setAiState] = useState<'analyzing' | 'done'>('analyzing');
  const [synthesis, setSynthesis] = useState<SynthesisResult | null>(null);
  const [synthesisState, setSynthesisState] = useState<'idle' | 'synthesizing' | 'done'>('idle');
  const [poleId, setPoleId] = useState(initialPoleId);
  // Sync when the parent resolves the nearest pole after GPS locks
  useEffect(() => {
    if (initialPoleId && initialPoleId !== 'Locating…') setPoleId(initialPoleId);
  }, [initialPoleId]);
  const [poleType, setPoleType] = useState('');
  const [classification, setClassification] = useState('');
  const [owner, setOwner] = useState('');
  const [circuit, setCircuit] = useState('');
  const [address, setAddress] = useState('');

  // Auto-fill pole metadata once when the nearest pole resolves — only fills empty fields
  const hasAutoFilledRef = useRef(false);
  useEffect(() => {
    if (!poleMetadata || hasAutoFilledRef.current) return;
    hasAutoFilledRef.current = true;
    if (poleMetadata.classification) setClassification(prev => prev || poleMetadata.classification!);
    if (poleMetadata.owner)          setOwner(prev => prev || poleMetadata.owner!);
    if (poleMetadata.circuit)        setCircuit(prev => prev || poleMetadata.circuit!);
    if (poleMetadata.address)        setAddress(prev => prev || poleMetadata.address!);
  }, [poleMetadata]);
  const [latStr, setLatStr] = useState(location ? location.lat.toFixed(6) : '');
  const [lonStr, setLonStr] = useState(location ? location.lon.toFixed(6) : '');
  const [severity, setSeverity] = useState<SeverityLevel>('medium');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancelledRef = useRef(false);

  const submittedPhotos = photos.map((photo) => ({ id: photo.id, label: photo.label, data_url: photo.dataUrl }));
  const doneAnalyses = photoAnalyses.filter((analysis) => !analysis.analyzing && !analysis.failed);

  function compressPhoto(dataUrl: string, maxPx = 512, quality = 0.65): Promise<string> {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        const ratio = Math.min(maxPx / img.width, maxPx / img.height, 1);
        const canvas = document.createElement('canvas');
        canvas.width = Math.round(img.width * ratio);
        canvas.height = Math.round(img.height * ratio);
        canvas.getContext('2d')?.drawImage(img, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL('image/jpeg', quality));
      };
      img.onerror = () => resolve(dataUrl);
      img.src = dataUrl;
    });
  }

  async function synthesizeResults(succeeded: PhotoAnalysis[], pType: string) {
    if (succeeded.length === 1) {
      const only = succeeded[0];
      setSynthesis({
        severity: only.severity,
        violations: only.violations,
        summary: only.recommendation,
        recommendation: only.recommendation,
        nesc: only.nesc,
        confidence: only.confidence,
        poweredBy: only.poweredBy,
      });
      setSynthesisState('done');
      return;
    }

    setSynthesisState('synthesizing');
    try {
      const resp = await fetch(`${API_BASE_URL}/api/dashboard/synthesize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pole_id: initialPoleId,
          pole_type: pType || null,
          analyses: succeeded.map((analysis) => ({
            photo_label: analysis.photoLabel,
            severity: analysis.severity,
            violations: analysis.violations,
            osha_class: analysis.oshaClass,
            nesc_rules: analysis.nesc,
            recommendation: analysis.recommendation,
            ai_score: analysis.confidence,
          })),
        }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      const nextSeverity = (data.severity as SeverityLevel) ?? 'medium';
      setSynthesis({
        severity: nextSeverity,
        violations: data.violations ?? [],
        summary: data.summary ?? '',
        recommendation: data.recommendation ?? '',
        nesc: data.nesc_rules ?? [],
        confidence: data.ai_score ?? 70,
        poweredBy: data.powered_by ?? 'watsonx.ai',
      });
      setSeverity(nextSeverity);
    } catch {
      const allViolations = [...new Set(succeeded.flatMap((analysis) => analysis.violations))];
      const worst = succeeded.reduce((currentWorst, analysis) => (
        SEV_ORDER.indexOf(analysis.severity) > SEV_ORDER.indexOf(currentWorst.severity) ? analysis : currentWorst
      ));
      setSynthesis({
        severity: worst.severity,
        violations: allViolations,
        summary: `${succeeded.length} photos analyzed. ${worst.recommendation}`,
        recommendation: worst.recommendation,
        nesc: [...new Set(succeeded.flatMap((analysis) => analysis.nesc))],
        confidence: Math.round(succeeded.reduce((sum, analysis) => sum + analysis.confidence, 0) / succeeded.length),
        poweredBy: 'merged fallback',
      });
      setSeverity(worst.severity);
    } finally {
      setSynthesisState('done');
    }
  }

  async function analyzeAllPhotos(desc: string, pType: string) {
    if (photos.length === 0) return;

    const photosToAnalyze = photos.slice(0, 3);
    cancelledRef.current = false;
    setSynthesis(null);
    setSynthesisState('idle');

    const initial: PhotoAnalysis[] = photosToAnalyze.map((photo) => ({
      photoId: photo.id,
      photoLabel: photo.label,
      tag: '',
      severity: 'medium',
      violations: [],
      oshaClass: 'other_than_serious',
      recommendation: '',
      nesc: [],
      confidence: 0,
      poweredBy: '',
      analyzing: true,
      failed: false,
    }));
    setPhotoAnalyses(initial);
    setAiState('analyzing');

    const results = [...initial];
    for (let i = 0; i < photosToAnalyze.length; i += 1) {
      if (cancelledRef.current) break;
      const photo = photosToAnalyze[i];
      try {
        const compressed = await compressPhoto(photo.dataUrl);
        if (cancelledRef.current) break;

        const resp = await fetch(`${API_BASE_URL}/api/dashboard/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            pole_id: initialPoleId,
            pole_type: pType || null,
            description: desc,
            photo_count: 1,
            photos: [compressed],
          }),
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        const nextSeverity = (data.severity as SeverityLevel) ?? 'medium';
        const violations: string[] = data.violations ?? [];
        results[i] = {
          photoId: photo.id,
          photoLabel: photo.label,
          tag: violationToTag(violations),
          severity: nextSeverity,
          violations,
          oshaClass: data.osha_class ?? 'other_than_serious',
          recommendation: data.recommendation ?? '',
          nesc: data.nesc_rules ?? [],
          confidence: data.ai_score ?? 70,
          poweredBy: data.powered_by ?? 'watsonx.ai',
          analyzing: false,
          failed: false,
        };
      } catch {
        results[i] = { ...results[i], tag: 'Error', analyzing: false, failed: true };
      }

      if (!cancelledRef.current) setPhotoAnalyses([...results]);
    }

    if (!cancelledRef.current) {
      const succeeded = results.filter((analysis) => !analysis.failed && !analysis.analyzing);
      if (succeeded.length) {
        setSeverity(worstSeverity(succeeded));
        setAiState('done');
        synthesizeResults(succeeded, pType);
      } else {
        setAiState('done');
      }
    }
  }

  function scheduleAnalysis(desc: string, pType: string) {
    if (timerRef.current) clearTimeout(timerRef.current);
    setAiState('analyzing');
    timerRef.current = setTimeout(() => analyzeAllPhotos(desc, pType), 800);
  }

  function analysisForSubmit(): AiFinding {
    if (!synthesis) return { ...FALLBACK_FINDING, severity };

    const activeViolations = synthesis.violations.filter((violation) => violation !== 'none' && violation !== 'unknown');
    const title = activeViolations.length
      ? activeViolations.slice(0, 3).map((violation) => violation.replace(/_/g, ' ')).join(' / ')
      : 'Field photo review';

    return {
      severity,
      finding: synthesis.summary || synthesis.recommendation || FALLBACK_FINDING.finding,
      confidence: synthesis.confidence,
      nesc: synthesis.nesc.length ? synthesis.nesc.join('; ') : FALLBACK_FINDING.nesc,
      action: synthesis.recommendation || FALLBACK_FINDING.action,
      dashboard_title: title,
      regulations: synthesis.nesc,
      evidence_required: FALLBACK_FINDING.evidence_required,
      specifications: { detected_violations: activeViolations.length },
    };
  }

  useEffect(() => {
    if (photos.length > 0) scheduleAnalysis(description, poleType);
    return () => {
      cancelledRef.current = true;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [photos.length]);

  function handleReplaceUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || replacingPhotoIndex === null) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataUrl = ev.target?.result as string;
      onPhotoReplace(replacingPhotoIndex, {
        id: crypto.randomUUID(),
        dataUrl,
        label: photos[replacingPhotoIndex]?.label ?? '',
      });
    };
    reader.readAsDataURL(file);
    setReplacingPhotoIndex(null);
    e.target.value = '';
  }

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
        photos: submittedPhotos,
        ai_analysis: analysisForSubmit(),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed. Check your connection and try again.');
      setSubmitting(false);
    }
  }

  return (
    <div className="sub-screen">
      <div className="sub-hdr">
        <button className="sub-ico-btn" onClick={onBack} aria-label="Back">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
          </svg>
        </button>
        <div className="sub-hdr-title">
          <span>Field report</span>
          <span className="sub-hdr-sub">Step 2 of 2 - Review &amp; submit</span>
        </div>
        <div style={{ width: 32 }} />
      </div>

      <div className="sub-review-body">
        <section className="sub-section">
          <h3 className="sub-section-label">Photos ({photos.length})</h3>
          <div className="fr-photo-grid">
            {photos.map((photo, index) => {
              const analysis = photoAnalyses[index];
              const tagColor = analysis && !analysis.analyzing && !analysis.failed ? SEV[analysis.severity].border : '#374151';
              const tagText = analysis ? (analysis.analyzing ? '...' : analysis.tag || 'No issues') : '';
              return (
                <div key={photo.id} className="fr-photo-thumb">
                  <img src={photo.dataUrl} alt={photo.label} />
                  <span className="fr-photo-lbl">{photo.label}</span>
                  {tagText && <span className="fr-photo-tag" style={{ background: tagColor }}>{tagText}</span>}
                  <button
                    className="fr-photo-replace"
                    aria-label={`Replace ${photo.label} photo`}
                    onClick={() => { setReplacingPhotoIndex(index); replaceInputRef.current?.click(); }}
                  >
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                      <circle cx="12" cy="13" r="4" />
                    </svg>
                  </button>
                </div>
              );
            })}
          </div>
        </section>

        {photos.length > 0 && (
          <section className="fr-ai-panel">
            {aiState === 'analyzing' ? (
              <div className="fr-ai-hdr">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#93C5FD" strokeWidth="2" className="fr-spin">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                </svg>
                Analyzing {photos.length} photo{photos.length !== 1 ? 's' : ''}...
                {doneAnalyses.length > 0 && (
                  <span style={{ fontSize: 11, color: '#60A5FA', marginLeft: 6 }}>
                    ({doneAnalyses.length} of {photoAnalyses.length} done)
                  </span>
                )}
              </div>
            ) : synthesisState === 'synthesizing' ? (
              <div className="fr-ai-hdr">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#93C5FD" strokeWidth="2" className="fr-spin">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                </svg>
                Synthesizing {doneAnalyses.length} findings into one assessment...
              </div>
            ) : synthesis ? (
              <>
                <div className="fr-ai-hdr">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#93C5FD" strokeWidth="2">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                  </svg>
                  Unified pole assessment - {doneAnalyses.length} photo{doneAnalyses.length !== 1 ? 's' : ''}
                  <span className="fr-ai-confidence">{synthesis.confidence}% confidence</span>
                  <span style={{ marginLeft: 'auto', fontSize: 9, color: '#4B5563' }}>{synthesis.poweredBy}</span>
                </div>
                {synthesis.summary && <p className="fr-ai-finding">{synthesis.summary}</p>}
                {synthesis.violations.filter((violation) => violation !== 'none' && violation !== 'unknown').length > 0 && (
                  <p style={{ margin: '4px 0 0', fontSize: 12, color: '#93C5FD', lineHeight: 1.45 }}>
                    <strong style={{ color: '#DBEAFE' }}>Violations: </strong>
                    {synthesis.violations
                      .filter((violation) => violation !== 'none' && violation !== 'unknown')
                      .map((violation) => violation.replace(/_/g, ' '))
                      .join(' - ')}
                  </p>
                )}
                <div className="fr-ai-meta">
                  {synthesis.nesc.length > 0 && (
                    <span className="fr-ai-nesc">
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
                      </svg>
                      {synthesis.nesc.join(' - ')}
                    </span>
                  )}
                  {synthesis.recommendation && <span className="fr-ai-action">{synthesis.recommendation}</span>}
                </div>
                <p className="fr-ai-nudge">
                  Recommended severity:{' '}
                  <strong style={{ color: SEV[synthesis.severity].color }}>{SEV[synthesis.severity].label}</strong>.
                  Adjust below if needed.
                </p>
              </>
            ) : null}
          </section>
        )}

        {photoAnalyses.length > 0 && (
          <section className="sub-section">
            <h3 className="sub-section-label">Photo breakdown</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {photoAnalyses.map((analysis, index) => (
                <div
                  key={analysis.photoId}
                  className="fr-photo-result"
                  style={{ borderColor: analysis.analyzing ? '#1F2937' : SEV[analysis.severity].border }}
                >
                  <div className="fr-photo-result-hdr">
                    <span style={{ fontSize: 12, fontWeight: 600, color: '#CBD5E1' }}>
                      Photo {index + 1} - {analysis.photoLabel}
                    </span>
                    {analysis.analyzing ? (
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: '#64748B' }}>
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#93C5FD" strokeWidth="2" className="fr-spin">
                          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                        </svg>
                        Analyzing...
                      </span>
                    ) : analysis.failed ? (
                      <span style={{ fontSize: 11, color: '#FCA5A5' }}>Analysis failed</span>
                    ) : (
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 700,
                          color: SEV[analysis.severity].color,
                          background: SEV[analysis.severity].bg,
                          border: `1px solid ${SEV[analysis.severity].border}`,
                          borderRadius: 4,
                          padding: '1px 7px',
                        }}
                      >
                        {SEV[analysis.severity].label}
                      </span>
                    )}
                  </div>
                  {!analysis.analyzing && !analysis.failed && (
                    <>
                      <p style={{ margin: '7px 0 0', fontSize: 12, color: '#BFDBFE', lineHeight: 1.5 }}>
                        {analysis.violations.filter((violation) => violation !== 'none' && violation !== 'unknown').length > 0
                          ? analysis.violations
                              .filter((violation) => violation !== 'none' && violation !== 'unknown')
                              .map((violation) => violation.replace(/_/g, ' '))
                              .join(' - ')
                          : 'No violations detected'}
                      </p>
                      <p style={{ margin: '4px 0 0', fontSize: 12, color: '#93C5FD', lineHeight: 1.45 }}>
                        {analysis.recommendation}
                      </p>
                      {analysis.nesc.length > 0 && (
                        <p style={{ margin: '5px 0 0', fontSize: 10, color: '#60A5FA', opacity: 0.85 }}>
                          {analysis.nesc.slice(0, 3).join(' - ')}
                        </p>
                      )}
                      <p style={{ margin: '4px 0 0', fontSize: 10, color: '#4B5563' }}>
                        {analysis.confidence}% confidence
                      </p>
                    </>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="sub-section">
          <h3 className="sub-section-label">Severity</h3>
          <div className="fr-sev-row">
            {(['critical', 'high', 'medium', 'low'] as SeverityLevel[]).map((item) => {
              const meta = SEV[item];
              const active = severity === item;
              return (
                <button
                  key={item}
                  className={`fr-sev-btn${active ? ' active' : ''}`}
                  style={active ? { borderColor: meta.border, background: meta.bg, color: meta.color } : {}}
                  onClick={() => setSeverity(item)}
                >
                  {meta.label}
                </button>
              );
            })}
          </div>
        </section>

        <section className="sub-section">
          <h3 className="sub-section-label">Pole identity</h3>
          <div className="fr-field-group">
            <label className="fr-label">Pole ID</label>
            <input className="fr-input" value={poleId} onChange={(e) => setPoleId(e.target.value)} placeholder="e.g. P-1147" />
          </div>
          <div className="fr-field-group">
            <label className="fr-label">Pole type</label>
            <select
              className="fr-select"
              value={poleType}
              onChange={(e) => {
                setPoleType(e.target.value);
                scheduleAnalysis(description, e.target.value);
              }}
            >
              {POLE_TYPES.map((type) => <option key={type.id} value={type.id}>{type.label}</option>)}
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

        <section className="sub-section">
          <h3 className="sub-section-label">Location</h3>
          {location && (
            <div className="fr-gps-badge">
              <span className="fr-pulse" />
              GPS captured - +/-{location.accuracy.toFixed(1)} m accuracy
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

        <section className="sub-section">
          <h3 className="sub-section-label">
            Description <span className="sub-section-opt">(optional)</span>
          </h3>
          <textarea
            className="sub-textarea"
            placeholder="Describe what you observed - damage type, extent, any immediate safety hazard..."
            value={description}
            onChange={(e) => {
              setDescription(e.target.value);
              scheduleAnalysis(e.target.value, poleType);
            }}
            rows={4}
            maxLength={1000}
          />
          <div className="sub-char-count">{description.length} / 1000</div>
        </section>

        {error && <p className="sub-error">{error}</p>}

        <input ref={replaceInputRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleReplaceUpload} />

        <button className="fr-submit-btn" onClick={handleSubmit} disabled={submitting}>
          {submitting ? (
            <>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="fr-spin">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              Submitting...
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
