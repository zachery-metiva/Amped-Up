import { useState } from 'react';
import { FieldCaptureStep } from '../components/fieldreport/FieldCaptureStep';
import { FieldReviewStep, FieldReportPayload } from '../components/fieldreport/FieldReviewStep';
import { CapturedPhoto, GpsCoords } from '../types/submission';
import { randomPoleId } from '../utils/randomPole';
import '../submission.css';
import '../field-report.css';

const DEFAULT_POLE_ID = new URLSearchParams(window.location.search).get('pole') ?? randomPoleId();

export function FieldReport() {
  const [step, setStep] = useState<'capture' | 'review'>('capture');
  const [photos, setPhotos] = useState<CapturedPhoto[]>([]);
  const [location, setLocation] = useState<GpsCoords | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [submittedPoleId, setSubmittedPoleId] = useState('');
  const [submittedSeverity, setSubmittedSeverity] = useState('');
  const [submittedPhotoCount, setSubmittedPhotoCount] = useState(0);

  function handlePhotoCapture(photo: CapturedPhoto) {
    setPhotos((prev) => [...prev, photo]);
  }

  async function handleSubmit(payload: FieldReportPayload) {
    const res = await fetch('/api/dashboard/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    setSubmittedPoleId(payload.pole_id || DEFAULT_POLE_ID);
    setSubmittedSeverity(payload.severity);
    setSubmittedPhotoCount(payload.photo_count);
    setSubmitted(true);
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
          <a href="/" className="fr-done-btn">Back to dashboard</a>
        </div>
      </div>
    );
  }

  if (step === 'capture') {
    return (
      <FieldCaptureStep
        poleId={DEFAULT_POLE_ID}
        photos={photos}
        location={location}
        onPhotoCapture={handlePhotoCapture}
        onLocationUpdate={setLocation}
        onContinue={() => setStep('review')}
      />
    );
  }

  return (
    <FieldReviewStep
      poleId={DEFAULT_POLE_ID}
      photos={photos}
      location={location}
      onBack={() => setStep('capture')}
      onSubmit={handleSubmit}
    />
  );
}
