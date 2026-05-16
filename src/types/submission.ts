export interface CapturedPhoto {
  id: string;
  dataUrl: string;
  label: string;
}

export interface GpsCoords {
  lat: number;
  lon: number;
  accuracy: number;
}

export type SubmissionStep = 'capture' | 'review';

export interface SubmissionState {
  step: SubmissionStep;
  poleId: string;
  photos: CapturedPhoto[];
  location: GpsCoords | null;
  description: string;
}

export interface SubmitReportPayload {
  pole_id: string;
  location: { lat: number; lon: number; accuracy: number } | null;
  description: string;
  photo_count: number;
}
