import { useState } from 'react';
import { CaptureStep } from '../components/submission/CaptureStep';
import { ReviewStep } from '../components/submission/ReviewStep';
import { SafetyModal } from '../components/submission/SafetyModal';
import { CapturedPhoto, GpsCoords, SubmissionStep, SubmitReportPayload } from '../types/submission';
import { randomPoleId } from '../utils/randomPole';
import { DASHBOARD_API_URL } from '../config/api';
import '../submission.css';

const DEFAULT_POLE_ID = new URLSearchParams(window.location.search).get('pole') ?? randomPoleId();

async function responseError(res: Response): Promise<Error> {
  try {
    const body = await res.json();
    const detail = typeof body.detail === 'string' ? body.detail : `Server returned ${res.status}`;
    return new Error(detail);
  } catch {
    return new Error(`Server returned ${res.status}`);
  }
}

export function ReportSubmission() {
  const [safetyAcknowledged, setSafetyAcknowledged] = useState(false);
  const [step, setStep] = useState<SubmissionStep>('capture');
  const [photos, setPhotos] = useState<CapturedPhoto[]>([]);
  const [location, setLocation] = useState<GpsCoords | null>(null);
  const [description, setDescription] = useState('');
  const [submitted, setSubmitted] = useState(false);

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

  async function handleSubmit(payload: SubmitReportPayload) {
    const res = await fetch(`${DASHBOARD_API_URL}/reports?cache_bust=${Date.now()}`, {
      method: 'POST',
      cache: 'no-store',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw await responseError(res);
    setSubmitted(true);
  }

  if (!safetyAcknowledged) {
    return <SafetyModal onAcknowledge={() => setSafetyAcknowledged(true)} />;
  }

  if (submitted) {
    return (
      <div className="sub-screen sub-done">
        <div className="sub-done-inner">
          <div className="sub-done-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#86EFAC" strokeWidth="1.5">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
          <h2 className="sub-done-title">Report submitted</h2>
          <p className="sub-done-sub">
            Pole {DEFAULT_POLE_ID} — {photos.length} photo{photos.length !== 1 ? 's' : ''} uploaded.
            The ops team will review and prioritize this report.
          </p>
          <a href="/" className="sub-done-btn">Back to dashboard</a>
        </div>
      </div>
    );
  }

  if (step === 'capture') {
    return (
      <CaptureStep
        poleId={DEFAULT_POLE_ID}
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
    <ReviewStep
      poleId={DEFAULT_POLE_ID}
      photos={photos}
      location={location}
      description={description}
      onDescriptionChange={setDescription}
      onPhotoReplace={handlePhotoReplace}
      onBack={() => setStep('capture')}
      onSubmit={handleSubmit}
    />
  );
}
