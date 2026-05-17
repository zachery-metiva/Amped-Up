import { useEffect, useRef, useState } from 'react';
import { CapturedPhoto, GpsCoords } from '../../types/submission';

const PHOTO_SLOTS: { label: string; shortLabel: string }[] = [
  { label: 'Wide overview', shortLabel: 'Overview' },
  { label: 'Damage closeup', shortLabel: 'Damage' },
  { label: 'Base of pole', shortLabel: 'Base' },
];

interface FieldCaptureStepProps {
  poleId: string;
  photos: CapturedPhoto[];
  location: GpsCoords | null;
  onPhotoCapture: (photo: CapturedPhoto) => void;
  onPhotoReplace: (index: number, photo: CapturedPhoto) => void;
  onLocationUpdate: (coords: GpsCoords) => void;
  onContinue: () => void;
}

export function FieldCaptureStep({
  poleId,
  photos,
  location,
  onPhotoCapture,
  onPhotoReplace,
  onLocationUpdate,
  onContinue,
}: FieldCaptureStepProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [replacingSlotIndex, setReplacingSlotIndex] = useState<number | null>(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [gpsStatus, setGpsStatus] = useState<'pending' | 'locked' | 'error'>('pending');
  const [facingMode, setFacingMode] = useState<'environment' | 'user'>('environment');

  const activeSlotIndex = photos.length;
  const allTaken = photos.length >= PHOTO_SLOTS.length;
  const canContinue = photos.length >= 1;
  const retakeMode = replacingSlotIndex !== null;
  const cameraPaused = canContinue && !retakeMode;
  const shouldUseCamera = !cameraPaused;

  function stopCamera() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraReady(false);
  }

  // Camera
  useEffect(() => {
    let active = true;
    async function start() {
      if (!shouldUseCamera) {
        stopCamera();
        return;
      }

      stopCamera();
      setCameraReady(false);
      setCameraError(null);
      setPermissionDenied(false);
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode, width: { ideal: 1280 }, height: { ideal: 960 } },
          audio: false,
        });
        if (!active) { stream.getTracks().forEach((t) => t.stop()); return; }
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
      stopCamera();
    };
  }, [facingMode, retryCount, shouldUseCamera]);

  // GPS watch
  useEffect(() => {
    if (!navigator.geolocation) { setGpsStatus('error'); return; }
    const watchId = navigator.geolocation.watchPosition(
      (pos) => {
        setGpsStatus('locked');
        onLocationUpdate({ lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy: pos.coords.accuracy });
      },
      () => setGpsStatus('error'),
      { enableHighAccuracy: true, timeout: 15_000, maximumAge: 5_000 },
    );
    return () => navigator.geolocation.clearWatch(watchId);
  }, [onLocationUpdate]);

  function capture() {
    if (!videoRef.current || !canvasRef.current) return;
    if (!retakeMode && allTaken) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 960;
    canvas.getContext('2d')?.drawImage(video, 0, 0);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    if (retakeMode) {
      const slot = PHOTO_SLOTS[replacingSlotIndex];
      onPhotoReplace(replacingSlotIndex, { id: crypto.randomUUID(), dataUrl, label: slot.shortLabel });
      setReplacingSlotIndex(null);
    } else {
      const slot = PHOTO_SLOTS[activeSlotIndex];
      onPhotoCapture({ id: crypto.randomUUID(), dataUrl, label: slot.shortLabel });
    }
    stopCamera();
  }

  function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    files.slice(0, PHOTO_SLOTS.length - photos.length).forEach((file, i) => {
      const reader = new FileReader();
      reader.onload = (ev) => {
        const dataUrl = ev.target?.result as string;
        const slot = PHOTO_SLOTS[photos.length + i] ?? PHOTO_SLOTS[PHOTO_SLOTS.length - 1];
        onPhotoCapture({ id: crypto.randomUUID(), dataUrl, label: slot.shortLabel });
      };
      reader.readAsDataURL(file);
    });
    e.target.value = '';
  }

  return (
    <div className="sub-screen">
      {/* Header */}
      <div className="sub-hdr">
        <a href="/" className="sub-ico-btn" aria-label="Close">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </a>
        <div className="sub-hdr-title">
          <span>Field report</span>
          <span className="sub-hdr-sub">Step 1 of 2 · Capture</span>
        </div>
        <button className="sub-ico-btn" aria-label="Help">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </button>
      </div>

      {/* Viewfinder */}
      <div className="sub-viewfinder">
        {cameraPaused ? (
          <div className="sub-cam-error">
            {photos[0] && <img src={photos[0].dataUrl} alt={photos[0].label} className="sub-paused-photo" />}
            <p>Camera paused after capture.</p>
          </div>
        ) : cameraError ? (
          <div className="sub-cam-error">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="1.5">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
            <p>{cameraError}</p>
            {permissionDenied && (
              <button
                className="sub-cap-btn"
                style={{ width: 'auto', borderRadius: 10, padding: '10px 20px', fontSize: 13, background: '#1D4ED8', outline: '2px solid #1D4ED8', color: '#fff' }}
                onClick={() => setRetryCount(c => c + 1)}
              >
                Request camera access
              </button>
            )}
            <button
              className="sub-cap-btn"
              style={{ width: 'auto', borderRadius: 10, padding: '10px 20px', fontSize: 13 }}
              onClick={() => fileInputRef.current?.click()}
            >
              Upload photos
            </button>
          </div>
        ) : (
          <video ref={videoRef} autoPlay playsInline muted className="sub-video" />
        )}

        {/* Corner frame */}
        <svg className="sub-frame" viewBox="0 0 300 380" aria-hidden="true">
          <g stroke="#FBBF24" strokeWidth="2.5" fill="none">
            <path d="M30,40 L30,64 M30,40 L54,40" />
            <path d="M270,40 L270,64 M270,40 L246,40" />
            <path d="M30,330 L30,306 M30,330 L54,330" />
            <path d="M270,330 L270,306 M270,330 L246,330" />
          </g>
        </svg>

        {/* GPS chips */}
        <div className="sub-gps-stack">
          <span className={`sub-chip${gpsStatus === 'locked' ? ' live' : ''}`}>
            {gpsStatus === 'locked' ? (
              <><span className="sub-pulse" /><span>GPS locked</span></>
            ) : gpsStatus === 'error' ? (
              <>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <span>GPS unavailable</span>
              </>
            ) : (
              <>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                </svg>
                <span>Acquiring GPS…</span>
              </>
            )}
          </span>
          {location && (
            <>
              <span className="sub-chip">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
                </svg>
                {location.lat.toFixed(4)}° N, {Math.abs(location.lon).toFixed(4)}° W
              </span>
              <span className="sub-chip">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="3" />
                </svg>
                ±{location.accuracy.toFixed(1)} m accuracy
              </span>
            </>
          )}
        </div>

        {/* Pole tag */}
        <div className="sub-pole-tag">
          <span className="sub-chip">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#86EFAC" strokeWidth="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            Pole {poleId}
          </span>
        </div>

        {/* Tip */}
        {retakeMode ? (
          <div className="sub-tip sub-tip-retake">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#FBBF24" strokeWidth="2" style={{ flexShrink: 0, marginTop: 1 }}>
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
            <div>
              <strong style={{ color: '#FDE68A', fontWeight: 500 }}>
                Retaking {PHOTO_SLOTS[replacingSlotIndex].shortLabel}.
              </strong>{' '}
              <span style={{ color: '#92400E' }}>Tap the shutter to replace it.</span>
            </div>
          </div>
        ) : !canContinue && (
          <div className="sub-tip">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" strokeWidth="2" style={{ flexShrink: 0, marginTop: 1 }}>
              <line x1="12" y1="2" x2="12" y2="6" /><line x1="12" y1="18" x2="12" y2="22" />
              <line x1="4.93" y1="4.93" x2="7.76" y2="7.76" /><line x1="16.24" y1="16.24" x2="19.07" y2="19.07" />
              <line x1="2" y1="12" x2="6" y2="12" /><line x1="18" y1="12" x2="22" y2="12" />
              <line x1="4.93" y1="19.07" x2="7.76" y2="16.24" /><line x1="16.24" y1="7.76" x2="19.07" y2="4.93" />
            </svg>
            <div>
              <strong style={{ color: '#DBEAFE', fontWeight: 500 }}>
                {PHOTO_SLOTS[activeSlotIndex]?.label}.
              </strong>{' '}
              {activeSlotIndex === 0 && 'Step back to get the full pole in frame.'}
              {activeSlotIndex === 1 && 'Move in close to show the damage clearly. '}
              {activeSlotIndex === 2 && 'Capture the ground contact and any soil disturbance. '}
              {activeSlotIndex > 0 && (
                <span style={{ color: '#64748B' }}>Optional — you can continue now.</span>
              )}
            </div>
          </div>
        )}

        {/* Photo slots */}
        <div className="sub-slots">
          {PHOTO_SLOTS.map((slot, i) => {
            const taken = i < photos.length;
            const active = i === activeSlotIndex && !canContinue;
            const isRetaking = replacingSlotIndex === i;
            return (
              <div
                key={slot.shortLabel}
                className={`sub-slot${taken ? ' done' : active ? ' active' : ''}${isRetaking ? ' retaking' : ''}`}
                onClick={taken ? () => setReplacingSlotIndex((prev) => (prev === i ? null : i)) : undefined}
                title={taken ? (isRetaking ? 'Cancel retake' : `Tap to retake ${slot.shortLabel}`) : undefined}
              >
                {taken ? (
                  <img src={photos[i].dataUrl} alt={slot.shortLabel} className="sub-slot-thumb" />
                ) : active ? (
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                    <circle cx="12" cy="13" r="4" />
                  </svg>
                ) : (
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <circle cx="12" cy="12" r="10" />
                  </svg>
                )}
                <span className="sub-slot-num">{i + 1}</span>
                <span className="sub-slot-lbl">
                  {slot.shortLabel}
                  {i > 0 && !taken && <span style={{ opacity: 0.45, fontSize: 8 }}> opt</span>}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Controls */}
      <div className="sub-controls">
        {/* Left: upload always available (up to max) */}
        <button
          className="sub-ico-btn"
          aria-label="Upload photo"
          onClick={() => fileInputRef.current?.click()}
          disabled={allTaken}
          title="Upload from gallery"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </button>

        {/* Center: shutter (up to 3) or big Continue (all 3 taken) */}
        {canContinue && !retakeMode ? (
          <button className="sub-continue-btn" onClick={onContinue}>
            Continue
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
            </svg>
          </button>
        ) : (
          <button className="sub-cap-btn" onClick={capture} disabled={!cameraReady} aria-label="Take photo">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
          </button>
        )}

        {/* Right: compact Continue (1–2 photos) or flip (0 photos / all taken) */}
        {cameraPaused ? (
          <span className="sub-control-spacer" aria-hidden="true" />
        ) : (
          <button
            className="sub-ico-btn"
            onClick={() => setFacingMode((m) => m === 'environment' ? 'user' : 'environment')}
            aria-label="Flip camera"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="1 4 1 10 7 10" /><polyline points="23 20 23 14 17 14" />
              <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
            </svg>
          </button>
        )}
      </div>

      <input ref={fileInputRef} type="file" accept="image/*" multiple style={{ display: 'none' }} onChange={handleUpload} />
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  );
}
