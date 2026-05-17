import 'leaflet/dist/leaflet.css';
import { useEffect, useRef, useState } from 'react';
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap } from 'react-leaflet';
import { CapturedPhoto, GpsCoords } from '../../types/submission';
import { API_BASE_URL } from '../../config/api';
import type { FieldReportPayload } from './FieldReviewStep';

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
  high:     { label: 'High',     color: '#FED7AA', bg: '#431407', border: '#F97316' },
  medium:   { label: 'Medium',   color: '#FDE68A', bg: '#451A03', border: '#FBBF24' },
  low:      { label: 'Low',      color: '#BBF7D0', bg: '#052E16', border: '#22C55E' },
};

const SEV_ORDER: SeverityLevel[] = ['low', 'medium', 'high', 'critical'];

const VIOLATION_TAGS: Record<string, string> = {
  transformer_oil_leak:              'Oil leak',
  recloser_oil_leak:                 'Oil leak',
  crossarm_split:                    'Crossarm split',
  crossarm_decay:                    'Crossarm decay',
  pole_lean_excessive:               'Lean',
  stub_lean_excessive:               'Lean',
  groundline_decay:                  'Decay',
  pole_decay_groundline:             'Decay',
  pole_decay_woodpecker:             'Decay',
  vegetation_contact_primary:        'Veg. contact',
  vegetation_contact_phase_a:        'Veg. contact',
  vegetation_contact_transmission:   'Veg. contact',
  vegetation_encroachment_primary:   'Veg. encroach.',
  tall_vegetation_in_row:            'Tall vegetation',
  guy_strand_corroded:               'Guy corrosion',
  guy_strand_corrosion:              'Guy corrosion',
  anchor_pulled:                     'Anchor pulled',
  anchor_rod_exposed:                'Anchor exposed',
  insulator_arc_tracking:            'Arc tracking',
  polymer_insulator_tracking:        'Arc tracking',
  insulator_string_shattered:        'Shattered ins.',
  conductor_strand_break:            'Strand break',
  open_neutral:                      'Open neutral',
  downed_conductor_dead_end_failure: 'Down conductor',
  dead_end_clamp_failure_phase_c:    'Clamp failure',
  dead_end_clamp_slipped:            'Clamp slipped',
  loose_transformer_hardware:        'Loose hardware',
  loose_bank_hardware:               'Loose hardware',
  loose_tap_clamp:                   'Loose clamp',
  splice_thermal_damage:             'Thermal damage',
  riser_insulation_burned:           'Burned insul.',
  missing_equipment_ground:          'Missing ground',
  ground_lead_disconnected:          'Ground disconn.',
  cracked_bushing:                   'Cracked bushing',
  jumper_damaged:                    'Damaged jumper',
  bird_nest_on_equipment:            'Bird nest',
  bird_nest_on_recloser:             'Bird nest',
  unauthorized_attachment:           'Unauth. attach.',
  unauthorized_antenna_attachment:   'Unauth. antenna',
  id_tag_missing:                    'Missing ID tag',
  id_tag_illegible:                  'Faded ID tag',
  pole_id_faded:                     'Faded ID tag',
  graffiti:                          'Graffiti',
  none:                              'No issues',
};

function violationToTag(violations: string[]): string {
  const first = violations.find(v => v !== 'unknown') ?? 'none';
  if (first in VIOLATION_TAGS) return VIOLATION_TAGS[first];
  return first.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function worstSeverity(analyses: PhotoAnalysis[]): SeverityLevel {
  return analyses.reduce<SeverityLevel>((worst, a) =>
    SEV_ORDER.indexOf(a.severity) > SEV_ORDER.indexOf(worst) ? a.severity : worst,
    'low',
  );
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

const DETROIT: [number, number] = [42.3314, -83.0458];

/** Imperatively re-centers the map whenever `center` changes (MapContainer.center is mount-only). */
function MapRecenter({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, 17, { animate: true });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [center[0], center[1]]);
  return null;
}

const PHOTO_SLOTS: { label: string; shortLabel: string }[] = [
  { label: 'Wide overview', shortLabel: 'Overview' },
  { label: 'Damage closeup', shortLabel: 'Damage' },
  { label: 'Base of pole',   shortLabel: 'Base' },
];

const POLE_TYPES: { id: string; label: string }[] = [
  { id: '',           label: 'Unknown / not specified' },
  { id: 'sp35c5',    label: 'SP 35 ft Cls 5 - Single-phase rural' },
  { id: 'ju40c4',    label: 'JU 40 ft Cls 4 - Joint-use urban' },
  { id: 'de45c3',    label: 'DE 45 ft Cls 3 - Dead-end' },
  { id: 'daw46',     label: 'DAW 46 kV - Sub-transmission wood' },
  { id: 'serv30c6',  label: 'Serv 30 ft Cls 6 - Service pole' },
  { id: 'ang40c4',   label: 'ANG 40 ft Cls 4 - Angle pole' },
  { id: 'hfw69',     label: 'HFW 69 kV - H-frame wood' },
  { id: 'tap40c4',   label: 'TAP 40 ft Cls 4 - Tap pole' },
  { id: 'hfs138',    label: 'HFS 138 kV - H-frame steel' },
  { id: 'tds115',    label: 'TDS 115 kV - Transmission dead-end steel' },
  { id: 'bank45c3',  label: 'Bank 45 ft Cls 3 - Transformer bank' },
  { id: 'riser40c4', label: 'Riser 40 ft Cls 4 - Underground riser' },
  { id: 'other',     label: 'Other' },
];

interface NearestPole {
  id: string;
  lat: number;
  lon: number;
  severity: string;
  classification?: string;
  owner?: string;
  circuit?: string;
  address?: string;
}

interface FieldReportWideProps {
  poleId: string;
  onSubmit: (payload: FieldReportPayload) => Promise<void>;
}

export function FieldReportWide({ poleId: initialPoleId, onSubmit }: FieldReportWideProps) {
  /* ── Layout breakpoint ──────────────────────────────────────────── */
  const [windowWidth, setWindowWidth] = useState(
    typeof window !== 'undefined' ? window.innerWidth : 1280,
  );
  useEffect(() => {
    const handle = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handle);
    return () => window.removeEventListener('resize', handle);
  }, []);
  const isDesktop = windowWidth >= 1280;

  /* ── Photos & GPS ───────────────────────────────────────────────── */
  const [photos, setPhotos] = useState<CapturedPhoto[]>([]);
  const [location, setLocation] = useState<GpsCoords | null>(null);

  /* ── Camera ─────────────────────────────────────────────────────── */
  const videoRef   = useRef<HTMLVideoElement>(null);
  const canvasRef  = useRef<HTMLCanvasElement>(null);
  const streamRef  = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const replaceInputRef = useRef<HTMLInputElement>(null);
  const [replacingSlotIndex, setReplacingSlotIndex] = useState<number | null>(null);
  const [cameraReady,     setCameraReady]     = useState(false);
  const [cameraError,     setCameraError]     = useState<string | null>(null);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [retryCount,      setRetryCount]      = useState(0);
  const [gpsStatus,       setGpsStatus]       = useState<'pending' | 'locked' | 'error'>('pending');
  const [facingMode,      setFacingMode]       = useState<'environment' | 'user'>('environment');

  /* ── AI analysis ────────────────────────────────────────────────── */
  const [photoAnalyses,  setPhotoAnalyses]  = useState<PhotoAnalysis[]>([]);
  const [aiState,        setAiState]        = useState<'idle' | 'analyzing' | 'done'>('idle');
  const [synthesis,      setSynthesis]      = useState<SynthesisResult | null>(null);
  const [synthesisState, setSynthesisState] = useState<'idle' | 'synthesizing' | 'done'>('idle');
  const cancelledRef = useRef(false);

  /* ── Nearest pole ───────────────────────────────────────────────── */
  const [nearestPole, setNearestPole] = useState<NearestPole | null>(null);
  const fetchedNearestRef      = useRef(false);
  const locationInitialisedRef = useRef(false);

  /* ── Form ───────────────────────────────────────────────────────── */
  const [poleId,         setPoleId]         = useState(initialPoleId);
  const [poleType,       setPoleType]       = useState('');
  const [classification, setClassification] = useState('');
  const [owner,          setOwner]          = useState('');
  const [circuit,        setCircuit]        = useState('');
  const [address,        setAddress]        = useState('');
  const [latStr,         setLatStr]         = useState('');
  const [lonStr,         setLonStr]         = useState('');
  const [severity,       setSeverity]       = useState<SeverityLevel>('medium');
  const [description,    setDescription]    = useState('');
  const [submitting,     setSubmitting]     = useState(false);
  const [error,          setError]          = useState<string | null>(null);

  /* ── Camera effect (tablet only) ────────────────────────────────── */
  useEffect(() => {
    if (isDesktop) return;
    let active = true;

    async function start() {
      streamRef.current?.getTracks().forEach(t => t.stop());
      setCameraReady(false);
      setCameraError(null);
      setPermissionDenied(false);
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode, width: { ideal: 1280 }, height: { ideal: 960 } },
          audio: false,
        });
        if (!active) { stream.getTracks().forEach(t => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
        setCameraReady(true);
      } catch (err) {
        if (!active) return;
        const denied = err instanceof DOMException &&
          (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError');
        setPermissionDenied(denied);
        setCameraError(denied
          ? 'Camera access was denied.'
          : 'Camera unavailable — use Upload instead.');
      }
    }

    start();
    return () => {
      active = false;
      streamRef.current?.getTracks().forEach(t => t.stop());
    };
  }, [facingMode, retryCount, isDesktop]);

  /* ── GPS watch ──────────────────────────────────────────────────── */
  useEffect(() => {
    if (!navigator.geolocation) { setGpsStatus('error'); return; }
    const watchId = navigator.geolocation.watchPosition(
      pos => {
        setGpsStatus('locked');
        setLocation({
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        });
      },
      () => setGpsStatus('error'),
      { enableHighAccuracy: true, timeout: 15_000, maximumAge: 5_000 },
    );
    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  /* ── Nearest-pole fetch: fires once when location first becomes available ── */
  useEffect(() => {
    if (!location || fetchedNearestRef.current) return;
    fetchedNearestRef.current = true;
    fetch(`${API_BASE_URL}/api/dashboard/nearest-pole?lat=${location.lat}&lon=${location.lon}`)
      .then(r => r.ok ? r.json() : null)
      .then((data: NearestPole & { pole_id: string } | null) => {
        if (!data) return;
        setNearestPole({ id: data.pole_id, lat: data.lat, lon: data.lon, severity: data.severity });
        setPoleId(data.pole_id);
        // Auto-fill pole metadata — only set fields the tech hasn't touched yet
        if (data.classification) setClassification(prev => prev || data.classification!);
        if (data.owner)          setOwner(prev => prev || data.owner!);
        if (data.circuit)        setCircuit(prev => prev || data.circuit!);
        if (data.address)        setAddress(prev => prev || data.address!);
      })
      .catch(() => {});
  }, [location]);

  /* ── Auto-fill lat/lon once GPS first locks ─────────────────────── */
  useEffect(() => {
    if (!location || locationInitialisedRef.current) return;
    locationInitialisedRef.current = true;
    setLatStr(location.lat.toFixed(6));
    setLonStr(location.lon.toFixed(6));
  }, [location]);

  /* ── Trigger AI analysis whenever photos change ─────────────────── */
  useEffect(() => {
    if (photos.length === 0) return;
    cancelledRef.current = true;
    const snap  = [...photos];
    const pt    = poleType;
    const desc  = description;
    const tid   = setTimeout(() => {
      cancelledRef.current = false;
      analyzeAllPhotos(desc, pt, snap);
    }, 120);
    return () => clearTimeout(tid);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [photos.length, poleType]);

  /* ── Helpers ────────────────────────────────────────────────────── */
  function compressPhoto(dataUrl: string, maxPx = 512, quality = 0.65): Promise<string> {
    return new Promise(resolve => {
      const img = new Image();
      img.onload = () => {
        const ratio = Math.min(maxPx / img.width, maxPx / img.height, 1);
        const c = document.createElement('canvas');
        c.width  = Math.round(img.width  * ratio);
        c.height = Math.round(img.height * ratio);
        c.getContext('2d')!.drawImage(img, 0, 0, c.width, c.height);
        resolve(c.toDataURL('image/jpeg', quality));
      };
      img.onerror = () => resolve(dataUrl);
      img.src = dataUrl;
    });
  }

  async function synthesizeResults(succeeded: PhotoAnalysis[], pType: string) {
    if (succeeded.length < 2) {
      setSynthesis({
        severity:       succeeded[0].severity,
        violations:     succeeded[0].violations,
        summary:        succeeded[0].recommendation,
        recommendation: succeeded[0].recommendation,
        nesc:           succeeded[0].nesc,
        confidence:     succeeded[0].confidence,
        poweredBy:      succeeded[0].poweredBy,
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
          pole_id:   poleId,
          pole_type: pType || null,
          analyses: succeeded.map(a => ({
            photo_label:   a.photoLabel,
            severity:      a.severity,
            violations:    a.violations,
            osha_class:    a.oshaClass,
            nesc_rules:    a.nesc,
            recommendation: a.recommendation,
            ai_score:      a.confidence,
          })),
        }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      const sev = (data.severity as SeverityLevel) ?? 'medium';
      setSynthesis({
        severity:       sev,
        violations:     data.violations ?? [],
        summary:        data.summary ?? '',
        recommendation: data.recommendation ?? '',
        nesc:           data.nesc_rules ?? [],
        confidence:     data.ai_score ?? 70,
        poweredBy:      data.powered_by ?? 'watsonx.ai',
      });
      setSeverity(sev);
    } catch {
      const allViols = [...new Set(succeeded.flatMap(a => a.violations))];
      const worst = succeeded.reduce((w, a) =>
        SEV_ORDER.indexOf(a.severity) > SEV_ORDER.indexOf(w.severity) ? a : w,
      );
      setSynthesis({
        severity:       worst.severity,
        violations:     allViols,
        summary:        `${succeeded.length} photos analyzed. ${worst.recommendation}`,
        recommendation: worst.recommendation,
        nesc:           [...new Set(succeeded.flatMap(a => a.nesc))],
        confidence:     Math.round(succeeded.reduce((s, a) => s + a.confidence, 0) / succeeded.length),
        poweredBy:      'merged (synthesis unavailable)',
      });
    } finally {
      setSynthesisState('done');
    }
  }

  async function analyzeAllPhotos(
    desc: string,
    pType: string,
    photosSnap: CapturedPhoto[],
  ) {
    if (photosSnap.length === 0) return;
    cancelledRef.current = false;
    setSynthesis(null);
    setSynthesisState('idle');

    const initial: PhotoAnalysis[] = photosSnap.map(p => ({
      photoId: p.id, photoLabel: p.label, tag: '',
      severity: 'medium', violations: [], oshaClass: 'other_than_serious',
      recommendation: '', nesc: [], confidence: 0, poweredBy: '',
      analyzing: true, failed: false,
    }));
    setPhotoAnalyses(initial);
    setAiState('analyzing');

    const results = [...initial];

    for (let i = 0; i < photosSnap.length; i++) {
      if (cancelledRef.current) break;
      const photo = photosSnap[i];
      try {
        const compressed = await compressPhoto(photo.dataUrl);
        if (cancelledRef.current) break;
        const resp = await fetch(`${API_BASE_URL}/api/dashboard/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            pole_id:     poleId,
            pole_type:   pType || null,
            description: desc,
            photo_count: 1,
            photos:      [compressed],
          }),
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        const sev   = (data.severity as SeverityLevel) ?? 'medium';
        const viols: string[] = data.violations ?? [];
        results[i] = {
          photoId: photo.id, photoLabel: photo.label,
          tag: violationToTag(viols),
          severity: sev, violations: viols,
          oshaClass: data.osha_class ?? 'other_than_serious',
          recommendation: data.recommendation ?? '',
          nesc: data.nesc_rules ?? [],
          confidence: data.ai_score ?? 70,
          poweredBy: data.powered_by ?? 'watsonx.ai',
          analyzing: false, failed: false,
        };
      } catch {
        results[i] = { ...results[i], tag: 'Error', analyzing: false, failed: true };
      }
      if (!cancelledRef.current) setPhotoAnalyses([...results]);
    }

    if (!cancelledRef.current) {
      const succeeded = results.filter(r => !r.failed && !r.analyzing);
      if (succeeded.length) {
        setSeverity(worstSeverity(succeeded));
        setAiState('done');
        synthesizeResults(succeeded, pType);
      } else {
        setAiState('done');
      }
    }
  }

  function capture() {
    if (!videoRef.current || !canvasRef.current) return;
    const idx = photos.length;
    if (idx >= PHOTO_SLOTS.length) return;
    const video  = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width  = video.videoWidth  || 1280;
    canvas.height = video.videoHeight || 960;
    canvas.getContext('2d')?.drawImage(video, 0, 0);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    const slot = PHOTO_SLOTS[idx];
    setPhotos(prev => [...prev, { id: crypto.randomUUID(), dataUrl, label: slot.shortLabel }]);
  }

  function handleReplaceUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || replacingSlotIndex === null) return;
    const reader = new FileReader();
    reader.onload = ev => {
      const dataUrl = ev.target?.result as string;
      const slot = PHOTO_SLOTS[replacingSlotIndex];
      setPhotos(prev => {
        const next = [...prev];
        next[replacingSlotIndex] = { id: crypto.randomUUID(), dataUrl, label: slot.shortLabel };
        return next;
      });
    };
    reader.readAsDataURL(file);
    setReplacingSlotIndex(null);
    e.target.value = '';
  }

  function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    files.slice(0, PHOTO_SLOTS.length - photos.length).forEach((file, i) => {
      const reader = new FileReader();
      reader.onload = ev => {
        const dataUrl = ev.target?.result as string;
        const slot = PHOTO_SLOTS[photos.length + i] ?? PHOTO_SLOTS[PHOTO_SLOTS.length - 1];
        setPhotos(prev => [...prev, { id: crypto.randomUUID(), dataUrl, label: slot.shortLabel }]);
      };
      reader.readAsDataURL(file);
    });
    e.target.value = '';
  }

  function buildAiFinding(): AiFinding {
    if (!synthesis) return { ...FALLBACK_FINDING, severity };
    const activeViols = synthesis.violations.filter(v => v !== 'none' && v !== 'unknown');
    const title = activeViols.length
      ? activeViols.slice(0, 3).map(v => v.replace(/_/g, ' ')).join(' / ')
      : 'Field photo review';
    return {
      severity,
      finding:           synthesis.summary || synthesis.recommendation || FALLBACK_FINDING.finding,
      confidence:        synthesis.confidence,
      nesc:              synthesis.nesc.length ? synthesis.nesc.join('; ') : FALLBACK_FINDING.nesc,
      action:            synthesis.recommendation || FALLBACK_FINDING.action,
      dashboard_title:   title,
      regulations:       synthesis.nesc,
      evidence_required: FALLBACK_FINDING.evidence_required,
      specifications:    { detected_violations: activeViols.length },
    };
  }

  async function handleSubmit() {
    if (photos.length === 0 || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({
        pole_id:        poleId,
        pole_type:      poleType || null,
        classification: classification || null,
        owner:          owner || null,
        circuit:        circuit || null,
        address:        address || null,
        location:       latStr && lonStr
          ? { lat: parseFloat(latStr), lon: parseFloat(lonStr), accuracy: location?.accuracy ?? 0 }
          : location
            ? { lat: location.lat, lon: location.lon, accuracy: location.accuracy }
            : null,
        severity,
        description,
        photo_count:    photos.length,
        photos:         photos.map(p => ({ id: p.id, label: p.label, data_url: p.dataUrl })),
        ai_analysis:    buildAiFinding(),
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submission failed. Please try again.');
      setSubmitting(false);
    }
  }

  /* ── Derived state ──────────────────────────────────────────────── */
  const allTaken       = photos.length >= PHOTO_SLOTS.length;
  const activeSlotIdx  = photos.length;
  const canSubmit      = photos.length >= 1 && !submitting;

  /* ── Render ─────────────────────────────────────────────────────── */
  return (
    <div className={`frw-screen${isDesktop ? ' frw-desktop' : ''}`}>

      {/* ── Desktop top nav ── */}
      {isDesktop && (
        <nav className="frw-topnav">
          <div className="frw-logo">
            <div className="frw-logo-mark">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="#FBBF24" />
              </svg>
            </div>
            <span className="frw-logo-name">Amped Up</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ color: '#94A3B8', fontSize: 12 }}>Filing a report</span>
            <a href="/" className="frw-ico-btn" aria-label="Close">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </a>
          </div>
        </nav>
      )}

      {/* ── Tablet header ── */}
      {!isDesktop && (
        <div className="frw-hdr">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <a href="/" className="frw-ico-btn" aria-label="Back">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
              </svg>
            </a>
            <div>
              <div style={{ fontWeight: 500, color: '#E5E7EB', fontSize: 14 }}>Field report</div>
              <div style={{ fontSize: 11, color: '#64748B' }}>Capture &amp; review</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="frw-ico-btn" aria-label="Flash" disabled>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
            </button>
            <button
              className="frw-ico-btn"
              aria-label="Flip camera"
              onClick={() => setFacingMode(m => m === 'environment' ? 'user' : 'environment')}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="1 4 1 10 7 10" /><polyline points="23 20 23 14 17 14" />
                <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* ── Desktop page heading ── */}
      {isDesktop && (
        <div className="frw-desktop-head">
          <div>
            <div className="frw-h3" style={{ fontSize: 22 }}>New report</div>
            <div style={{ color: '#94A3B8', fontSize: 13, marginTop: 4 }}>
              Upload 3 photos, drop a pin on the location, and confirm severity.
            </div>
          </div>
        </div>
      )}

      {/* ── Two-panel body ── */}
      <div className="frw-body">

        {/* ════════════ LEFT PANEL ════════════ */}
        <div className="frw-left">
          {isDesktop ? (
            /* ── Desktop: upload grid + location map ── */
            <>
              {/* Photo upload section */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                  <div className="frw-h3">
                    Photos &middot; {photos.length}&nbsp;of&nbsp;3
                    {photos.length < 3 && <span style={{ color: '#64748B', fontWeight: 400, fontSize: 13 }}>&nbsp;required</span>}
                  </div>
                  <span style={{ fontSize: 11.5, color: '#94A3B8', display: 'flex', alignItems: 'center', gap: 5 }}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" /><path d="M12 8v4m0 4h.01" />
                    </svg>
                    Overview · damage · base of pole
                  </span>
                </div>
                <div className="frw-upload-grid">
                  {PHOTO_SLOTS.map((slot, i) => {
                    const taken = i < photos.length;
                    const an    = photoAnalyses[i];
                    return (
                      <div
                        key={slot.shortLabel}
                        className={`frw-drop-zone${taken ? ' filled' : ''}`}
                        onClick={() => {
                          if (taken) {
                            setReplacingSlotIndex(i);
                            replaceInputRef.current?.click();
                          } else {
                            fileInputRef.current?.click();
                          }
                        }}
                        title={taken ? `Click to replace ${slot.shortLabel}` : `Upload ${slot.label}`}
                      >
                        <span className="frw-drop-num">{i + 1}</span>
                        {taken ? (
                          <>
                            <img
                              src={photos[i].dataUrl}
                              alt={slot.shortLabel}
                              style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }}
                            />
                            {an && !an.analyzing && !an.failed && (
                              <span
                                className="frw-slot-violation"
                                style={{ background: SEV[an.severity].border }}
                              >
                                {an.tag}
                              </span>
                            )}
                            <span style={{
                              position: 'absolute', bottom: 6, left: 8,
                              fontSize: 10.5, color: '#86EFAC',
                              background: 'rgba(5,46,26,0.88)',
                              padding: '1px 6px', borderRadius: 3,
                            }}>
                              ✓ {slot.shortLabel}
                            </span>
                          </>
                        ) : (
                          <>
                            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                              <polyline points="16 16 12 12 8 16" />
                              <line x1="12" y1="12" x2="12" y2="21" />
                              <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
                            </svg>
                            <span className="frw-drop-name">{slot.label}</span>
                            <span className="frw-drop-hint">Drag and drop or click to upload</span>
                          </>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Location section */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                  <div className="frw-h3">Location</div>
                  {location ? (
                    <span className="frw-chip">
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#86EFAC" strokeWidth="2">
                        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
                      </svg>
                      {location.lat.toFixed(4)}° N, {Math.abs(location.lon).toFixed(4)}° W
                    </span>
                  ) : (
                    <span className="frw-chip" style={{ color: '#64748B' }}>
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                      </svg>
                      {gpsStatus === 'pending' ? 'Acquiring GPS…' : 'GPS unavailable'}
                    </span>
                  )}
                </div>
                <div className="frw-map-card">
                  <MapContainer
                    center={DETROIT}
                    zoom={17}
                    style={{ width: '100%', height: '100%' }}
                    scrollWheelZoom={false}
                    zoomControl={false}
                    attributionControl={false}
                  >
                    <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
                    <MapRecenter
                      center={nearestPole ? [nearestPole.lat, nearestPole.lon] : location ? [location.lat, location.lon] : DETROIT}
                    />
                    {nearestPole && (
                      <CircleMarker
                        center={[nearestPole.lat, nearestPole.lon]}
                        radius={9}
                        pathOptions={{ color: '#0B1020', fillColor: '#FBBF24', fillOpacity: 1, weight: 2 }}
                      >
                        <Tooltip direction="top" offset={[0, -10]} permanent>
                          <span style={{ fontWeight: 600 }}>{poleId}</span>
                        </Tooltip>
                      </CircleMarker>
                    )}
                    {location && (
                      <CircleMarker
                        center={[location.lat, location.lon]}
                        radius={6}
                        pathOptions={{ color: '#0B1020', fillColor: '#3B82F6', fillOpacity: 1, weight: 1.5 }}
                      />
                    )}
                  </MapContainer>
                </div>
                <div className="frw-addr-row">
                  <input
                    className="frw-addr-input"
                    placeholder="Address or intersection"
                    value={address}
                    onChange={e => setAddress(e.target.value)}
                  />
                  {location && (
                    <span className="frw-chip">
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="3" />
                      </svg>
                      ±{location.accuracy.toFixed(1)} m
                    </span>
                  )}
                </div>
              </div>
            </>
          ) : (
            /* ── Tablet: live camera viewfinder + capture row ── */
            <>
              <div className="frw-viewfinder">
                {cameraError ? (
                  <div className="frw-cam-error">
                    <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="1.5">
                      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                      <circle cx="12" cy="13" r="4" />
                    </svg>
                    <p style={{ margin: '6px 0', color: '#94A3B8' }}>{cameraError}</p>
                    {permissionDenied && (
                      <button
                        style={{
                          background: '#1D4ED8', color: '#fff', border: 'none',
                          borderRadius: 8, padding: '8px 16px', fontSize: 13,
                          cursor: 'pointer', marginBottom: 8, fontFamily: 'inherit',
                        }}
                        onClick={() => setRetryCount(c => c + 1)}
                      >
                        Request camera access
                      </button>
                    )}
                    <button
                      style={{
                        background: '#1F2937', color: '#D1D5DB',
                        border: '1px solid #374151', borderRadius: 8,
                        padding: '8px 16px', fontSize: 13, cursor: 'pointer', fontFamily: 'inherit',
                      }}
                      onClick={() => fileInputRef.current?.click()}
                    >
                      Upload photos
                    </button>
                  </div>
                ) : (
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                  />
                )}

                {/* Corner frame */}
                <svg
                  viewBox="0 0 300 380"
                  style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
                  aria-hidden="true"
                >
                  <g stroke="#FBBF24" strokeWidth="2.5" fill="none">
                    <path d="M30,40 L30,64 M30,40 L54,40" />
                    <path d="M270,40 L270,64 M270,40 L246,40" />
                    <path d="M30,330 L30,306 M30,330 L54,330" />
                    <path d="M270,330 L270,306 M270,330 L246,330" />
                  </g>
                </svg>

                {/* GPS chips */}
                <div className="frw-gps-stack">
                  <span className={`frw-chip${gpsStatus === 'locked' ? ' live' : ''}`}>
                    {gpsStatus === 'locked' ? (
                      <><span className="frw-pulse" /><span>GPS locked</span></>
                    ) : gpsStatus === 'error' ? (
                      <>
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                        </svg>
                        <span>GPS unavailable</span>
                      </>
                    ) : (
                      <>
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="12" cy="12" r="10" />
                        </svg>
                        <span>Acquiring GPS…</span>
                      </>
                    )}
                  </span>
                  {location && (
                    <>
                      <span className="frw-chip">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
                        </svg>
                        {location.lat.toFixed(4)}° N, {Math.abs(location.lon).toFixed(4)}° W
                      </span>
                      <span className="frw-chip">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="3" />
                        </svg>
                        ±{location.accuracy.toFixed(1)} m
                      </span>
                    </>
                  )}
                </div>

                {/* Pole tag */}
                <div className="frw-pole-tag">
                  <span className="frw-chip">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#86EFAC" strokeWidth="2">
                      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                    </svg>
                    {poleId === 'Locating…' ? 'Locating pole…' : `Pole ${poleId}`}
                  </span>
                </div>

                {/* Tip overlay */}
                {!allTaken && (
                  <div className="frw-tip-overlay">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" strokeWidth="2" style={{ flexShrink: 0, marginTop: 1 }}>
                      <circle cx="12" cy="12" r="10" /><path d="M12 8v4m0 4h.01" />
                    </svg>
                    <span>
                      <strong style={{ color: '#DBEAFE', fontWeight: 500 }}>
                        {PHOTO_SLOTS[activeSlotIdx]?.label}.
                      </strong>{' '}
                      {activeSlotIdx === 0 && 'Step back to get the full pole in frame.'}
                      {activeSlotIdx === 1 && 'Move in close to show the damage clearly.'}
                      {activeSlotIdx === 2 && 'Capture the ground contact and any soil disturbance.'}
                      {activeSlotIdx > 0 && (
                        <span style={{ color: '#475569' }}> Optional — right panel is ready.</span>
                      )}
                    </span>
                  </div>
                )}
              </div>

              {/* Capture row */}
              <div className="frw-capture-row">
                <div className="frw-slots-strip">
                  {PHOTO_SLOTS.map((slot, i) => {
                    const taken  = i < photos.length;
                    const active = i === activeSlotIdx && !allTaken;
                    const an     = photoAnalyses[i];
                    return (
                      <div
                        key={slot.shortLabel}
                        className={`frw-slot${taken ? ' done' : active ? ' active' : ''}`}
                        onClick={taken ? () => { setReplacingSlotIndex(i); replaceInputRef.current?.click(); } : undefined}
                        title={taken ? `Tap to replace ${slot.shortLabel}` : undefined}
                      >
                        {taken ? (
                          <>
                            <img src={photos[i].dataUrl} alt={slot.shortLabel} className="frw-slot-img" />
                            {an && !an.analyzing && !an.failed && (
                              <span
                                className="frw-slot-violation"
                                style={{ background: SEV[an.severity].border }}
                              >
                                {an.tag}
                              </span>
                            )}
                          </>
                        ) : active ? (
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                            <circle cx="12" cy="13" r="4" />
                          </svg>
                        ) : (
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <circle cx="12" cy="12" r="10" />
                          </svg>
                        )}
                        <span className="frw-slot-num">{i + 1}</span>
                        <span className="frw-slot-lbl">{slot.shortLabel}</span>
                      </div>
                    );
                  })}
                </div>

                <button
                  className={`frw-cap-btn${allTaken ? ' done' : ''}`}
                  onClick={capture}
                  disabled={!cameraReady || allTaken}
                  aria-label="Take photo"
                >
                  {allTaken ? (
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  ) : (
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                      <circle cx="12" cy="13" r="4" />
                    </svg>
                  )}
                </button>
              </div>
            </>
          )}
        </div>

        {/* ════════════ RIGHT PANEL ════════════ */}
        <div className="frw-right">
          {!isDesktop && (
            <div className="frw-h3">Report details</div>
          )}

          {/* Location card */}
          <div className="frw-card">
            <div className="frw-section-label">Location</div>
            <div className="frw-loc-card">
              <svg viewBox="0 0 60 60" className="frw-loc-mini-map">
                <defs>
                  <pattern id="frw-gp2" width="8" height="8" patternUnits="userSpaceOnUse">
                    <path d="M 8 0 L 0 0 0 8" fill="none" stroke="#1E293B" strokeWidth="0.5" />
                  </pattern>
                </defs>
                <rect width="60" height="60" fill="url(#frw-gp2)" />
                <line x1="0" y1="30" x2="60" y2="30" stroke="#1F2937" strokeWidth="2" />
                <line x1="30" y1="0" x2="30" y2="60" stroke="#1F2937" strokeWidth="2" />
                {location && (
                  <circle cx="30" cy="30" r="5" fill="#EF4444" stroke="#0B1020" strokeWidth="1.5" />
                )}
              </svg>
              <div style={{ fontSize: 12, lineHeight: 1.5 }}>
                {location ? (
                  <>
                    <div style={{ color: '#F9FAFB', fontWeight: 500 }}>
                      {poleId && poleId !== 'Locating…' ? `Pole ${poleId}` : 'GPS auto-captured'}
                    </div>
                    <div style={{ color: '#94A3B8' }}>
                      {location.lat.toFixed(4)}° N, {Math.abs(location.lon).toFixed(4)}° W
                    </div>
                    <div style={{ color: '#86EFAC', fontSize: 11, marginTop: 2 }}>
                      ✓ GPS locked · ±{location.accuracy.toFixed(1)} m
                    </div>
                  </>
                ) : (
                  <div style={{ color: '#94A3B8' }}>
                    {gpsStatus === 'pending' ? 'Acquiring GPS…' : 'GPS unavailable'}
                  </div>
                )}
              </div>
            </div>

            {/* Editable lat / lon */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 10 }}>
              <div>
                <div style={{ fontSize: 10, color: '#64748B', marginBottom: 3 }}>Latitude</div>
                <input
                  className="frw-input frw-mono"
                  value={latStr}
                  onChange={e => setLatStr(e.target.value)}
                  placeholder="42.331429"
                />
              </div>
              <div>
                <div style={{ fontSize: 10, color: '#64748B', marginBottom: 3 }}>Longitude</div>
                <input
                  className="frw-input frw-mono"
                  value={lonStr}
                  onChange={e => setLonStr(e.target.value)}
                  placeholder="-83.047530"
                />
              </div>
            </div>

            {/* Address (tablet only — desktop uses the left-panel input) */}
            {!isDesktop && (
              <div style={{ marginTop: 8 }}>
                <div style={{ fontSize: 10, color: '#64748B', marginBottom: 3 }}>Address / landmark</div>
                <input
                  className="frw-input"
                  value={address}
                  onChange={e => setAddress(e.target.value)}
                  placeholder="e.g. Michigan Ave & 12th St"
                />
              </div>
            )}
          </div>

          {/* AI suggestion card */}
          {(aiState !== 'idle' || synthesis) && (
            <div className="frw-ai-card">
              <div className="frw-ai-hd">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#93C5FD" strokeWidth="2">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                </svg>
                AI suggestion
              </div>
              {aiState === 'analyzing' ? (
                <span style={{ color: '#93C5FD' }}>
                  Analyzing photo{photos.length > 1 ? 's' : ''}&hellip;
                </span>
              ) : synthesisState === 'synthesizing' ? (
                <span style={{ color: '#93C5FD' }}>Synthesizing findings&hellip;</span>
              ) : synthesis ? (
                <>
                  <p style={{ margin: 0 }}>{synthesis.summary}</p>
                  {synthesis.severity && (
                    <div style={{ marginTop: 6, color: '#DBEAFE' }}>
                      Recommended severity:{' '}
                      <strong style={{ color: SEV[synthesis.severity].color }}>
                        {SEV[synthesis.severity].label}
                      </strong>. You can override below.
                    </div>
                  )}
                </>
              ) : null}
            </div>
          )}

          {/* Severity selector */}
          <div>
            <div className="frw-section-label">Severity</div>
            <div className="frw-sev-row">
              {(['critical', 'high', 'medium', 'low'] as SeverityLevel[]).map(s => (
                <button
                  key={s}
                  className="frw-sev-btn"
                  style={severity === s
                    ? { borderColor: SEV[s].border, background: SEV[s].bg, color: SEV[s].color }
                    : undefined}
                  onClick={() => setSeverity(s)}
                >
                  {SEV[s].label}
                </button>
              ))}
            </div>
          </div>

          {/* Pole ID + Reporter */}
          <div className="frw-pole-cards">
            <div className="frw-card">
              <div className="frw-section-label">Pole ID</div>
              <div style={{ fontSize: 14, color: '#F9FAFB', fontWeight: 500, display: 'flex', alignItems: 'center', gap: 7 }}>
                <input
                  value={poleId}
                  onChange={e => setPoleId(e.target.value)}
                  style={{
                    background: 'none', border: 'none', color: '#F9FAFB',
                    fontWeight: 500, fontSize: 14, outline: 'none',
                    fontFamily: 'inherit', width: '100%',
                  }}
                />
                <span style={{
                  fontSize: 10.5, padding: '2px 7px', borderRadius: 999,
                  background: '#1E3A5F', color: '#93C5FD',
                  border: '1px solid #1E40AF', whiteSpace: 'nowrap',
                }}>
                  Auto
                </span>
              </div>
            </div>
            <div className="frw-card">
              <div className="frw-section-label">Reported by</div>
              <div style={{ fontSize: 14, color: '#F9FAFB', fontWeight: 500, display: 'flex', alignItems: 'center', gap: 7 }}>
                <span style={{
                  width: 20, height: 20, borderRadius: '50%',
                  background: '#1E40AF', color: '#DBEAFE',
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 9.5, fontWeight: 500, flexShrink: 0,
                }}>
                  ZM
                </span>
                Z. Metiva
              </div>
            </div>
          </div>

          {/* Pole identity */}
          <div>
            <div className="frw-section-label">Pole identity</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <select
                className="frw-input frw-select"
                value={poleType}
                onChange={e => setPoleType(e.target.value)}
              >
                {POLE_TYPES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
              </select>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <input
                  className="frw-input"
                  value={classification}
                  onChange={e => setClassification(e.target.value)}
                  placeholder="Classification"
                />
                <input
                  className="frw-input"
                  value={owner}
                  onChange={e => setOwner(e.target.value)}
                  placeholder="Owner"
                />
              </div>
              <input
                className="frw-input"
                value={circuit}
                onChange={e => setCircuit(e.target.value)}
                placeholder="Circuit (e.g. CKT-04A)"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <div className="frw-section-label">
              Description{!isDesktop ? ' (optional)' : ''}
            </div>
            <textarea
              className="frw-note"
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder={isDesktop
                ? "Describe what you saw. For example: pole visibly leaning over the sidewalk after last night's storm, blocking pedestrian traffic."
                : 'Visible at impact location, blocking sidewalk.'}
              style={isDesktop ? { height: 110 } : undefined}
            />
          </div>

          {/* Error */}
          {error && (
            <div style={{
              background: '#3F0808', border: '1px solid #EF4444',
              borderRadius: 8, padding: '10px 12px',
              color: '#FECACA', fontSize: 12.5,
            }}>
              {error}
            </div>
          )}

          {/* Submit actions */}
          {isDesktop ? (
            <div className="frw-action-row">
              <button
                className="frw-submit"
                onClick={handleSubmit}
                disabled={!canSubmit}
              >
                {submitting ? 'Submitting…' : (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="22" y1="2" x2="11" y2="13" />
                      <polygon points="22 2 15 22 11 13 2 9 22 2" />
                    </svg>
                    Submit report
                  </>
                )}
              </button>
            </div>
          ) : (
            <button
              className="frw-submit"
              onClick={handleSubmit}
              disabled={!canSubmit}
            >
              {submitting ? 'Submitting…' : (
                <>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="22" y1="2" x2="11" y2="13" />
                    <polygon points="22 2 15 22 11 13 2 9 22 2" />
                  </svg>
                  Submit report
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Hidden canvas + file inputs */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        multiple
        style={{ display: 'none' }}
        onChange={handleUpload}
      />
      <input
        ref={replaceInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleReplaceUpload}
      />
    </div>
  );
}
