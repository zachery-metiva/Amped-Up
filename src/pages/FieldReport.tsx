import { useEffect, useRef, useState } from 'react';
import { FieldCaptureStep } from '../components/fieldreport/FieldCaptureStep';
import { FieldReviewStep, FieldReportPayload, PoleMetadata } from '../components/fieldreport/FieldReviewStep';
import { FieldReportWide } from '../components/fieldreport/FieldReportWide';
import { CapturedPhoto, GpsCoords } from '../types/submission';
import { randomPoleId } from '../utils/randomPole';
import { useWindowWidth } from '../hooks/useWindowWidth';
import { DASHBOARD_API_URL } from '../config/api';
import '../submission.css';
import '../field-report.css';

async function responseError(res: Response): Promise<Error> {
  try {
    const body = await res.json();
    const detail = typeof body.detail === 'string' ? body.detail : `Server returned ${res.status}`;
    return new Error(detail);
  } catch {
    return new Error(`Server returned ${res.status}`);
  }
}

export function FieldReport() {
  const [defaultPoleId, setDefaultPoleId] = useState(
    () => new URLSearchParams(window.location.search).get('pole') ?? randomPoleId(),
  );

  const windowWidth = useWindowWidth();
  const isWide = windowWidth >= 1024;
  const nearestFetchedRef = useRef(false);
  const [step, setStep] = useState<'capture' | 'review'>('capture');
  const [photos, setPhotos] = useState<CapturedPhoto[]>([]);
  const [location, setLocation] = useState<GpsCoords | null>(null);
  const [defaultPoleMetadata, setDefaultPoleMetadata] = useState<PoleMetadata | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [submittedPoleId, setSubmittedPoleId] = useState('');
  const [submittedSeverity, setSubmittedSeverity] = useState('');
  const [submittedPhotoCount, setSubmittedPhotoCount] = useState(0);

  // Auto-resolve nearest pole when GPS first locks (mobile flow only)
  useEffect(() => {
    if (!location || nearestFetchedRef.current || isWide) return;
    nearestFetchedRef.current = true;
    fetch(`${DASHBOARD_API_URL}/nearest-pole?lat=${location.lat}&lon=${location.lon}`)
      .then(r => r.ok ? r.json() : null)
      .then((data: { pole_id: string; classification?: string; owner?: string; circuit?: string; address?: string } | null) => {
        if (!data?.pole_id) return;
        setDefaultPoleId(data.pole_id);
        setDefaultPoleMetadata({
          classification: data.classification ?? undefined,
          owner:          data.owner          ?? undefined,
          circuit:        data.circuit        ?? undefined,
          address:        data.address        ?? undefined,
        });
      })
      .catch(() => {});
  }, [location, isWide]);

  function handlePhotoCapture(photo: CapturedPhoto) {
    setPhotos((prev) => [...prev, photo]);
  }

  function handlePhotoReplace(index: number, photo: CapturedPhoto) {
    setPhotos((prev) => {
      const next = [...prev];
      next[index] = photo;
      return next;
    });
  }

  function resetForAnotherReport() {
    const routePoleId = new URLSearchParams(window.location.search).get('pole');
    setDefaultPoleId(routePoleId ?? randomPoleId());
    setDefaultPoleMetadata(null);
    nearestFetchedRef.current = false;
    setStep('capture');
    setPhotos([]);
    setLocation(null);
    setSubmitted(false);
    setSubmittedPoleId('');
    setSubmittedSeverity('');
    setSubmittedPhotoCount(0);
  }

  async function handleSubmit(payload: FieldReportPayload) {
    const res = await fetch(`${DASHBOARD_API_URL}/reports?cache_bust=${Date.now()}`, {
      method: 'POST',
      cache: 'no-store',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw await responseError(res);
    setSubmittedPoleId(payload.pole_id || defaultPoleId);
    setSubmittedSeverity(payload.severity);
    setSubmittedPhotoCount(payload.photo_count);
    setSubmitted(true);
  }

  /* ── Wide layout (tablet / desktop) ── */
  if (isWide && !submitted) {
    return (
      <FieldReportWide
        poleId={defaultPoleId}
        onSubmit={handleSubmit}
      />
    );
  }

  if (submitted) {
    const sevColors: Record<string, string> = {
      critical: '#FECACA', high: '#FED7AA', medium: '#FDE68A', low: '#BBF7D0',
    };
    return (
      <div className="sub-screen fr-done">
        <div className="fr-done-inner">
          <div className="fr-done-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#86EFAC" strokeWidth="1.5">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
          <h2 className="fr-done-title">Report submitted</h2>
          <p className="fr-done-sub">
            Pole {submittedPoleId || '—'} ·{' '}
            <span style={{ color: sevColors[submittedSeverity] ?? '#E5E7EB', fontWeight: 500 }}>
              {submittedSeverity.charAt(0).toUpperCase() + submittedSeverity.slice(1)}
            </span>
            {' '}· {submittedPhotoCount} photo{submittedPhotoCount !== 1 ? 's' : ''}.
            The ops team will review and prioritize.
          </p>
          <button type="button" className="fr-done-btn" onClick={resetForAnotherReport}>
            Submit another report
          </button>
          <a href="/" className="fr-done-btn">Back to dashboard</a>
        </div>
      </div>
    );
  }

  if (step === 'capture') {
    return (
      <FieldCaptureStep
        poleId={defaultPoleId}
        photos={photos}
        location={location}
        onPhotoCapture={handlePhotoCapture}
        onPhotoReplace={handlePhotoReplace}
        onLocationUpdate={setLocation}
        onContinue={() => setStep('review')}
      />
    );
  }

  return (
    <FieldReviewStep
      poleId={defaultPoleId}
      poleMetadata={defaultPoleMetadata}
      photos={photos}
      location={location}
      onPhotoReplace={handlePhotoReplace}
      onBack={() => setStep('capture')}
      onSubmit={handleSubmit}
    />
  );
}
