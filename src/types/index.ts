export type Severity = 'critical' | 'high' | 'medium' | 'low';
export type ReportStatus = 'open' | 'snoozed' | 'approved' | 'dismissed';
export type HistoryEventType =
  | 'report'
  | 'comment'
  | 'inspection'
  | 'upgrade'
  | 'joint_use'
  | 'treatment'
  | 'install'
  | 'other';

export interface User {
  initials: string;
  name: string;
  role: string;
  id: string;
}

export interface ReportAuthor {
  initials: string;
  name: string;
}

export interface DashboardSummary {
  totalPoles: number;
  newSinceLastScan: number;
  critical: number;
  high: number;
  medium: number;
  openReports: number;
  sector: string;
  date: string;
}

export interface Report {
  id: string;
  poleId: string;
  title: string;
  severity: Severity;
  submittedBy: ReportAuthor;
  submittedAt: string;
  location: string;
  status: ReportStatus;
}

export interface SelectedReport {
  id: string;
  poleId: string;
  title: string;
  severity: Severity;
  submittedBy: User;
  submittedAt: string;
}

export interface PoleDetail {
  id: string;
  classification: string;
  severity: Severity;
  address: string;
  lat: number;
  lon: number;
  height: string;
  owner: string;
  circuit: string;
  lean: string | null;
  aiScore: number;
  aiConfidence: string;
  recommendation: string;
}

export interface FieldPhoto {
  id: string;
  label: string;
  severity: Severity | null;
  severityLabel: string | null;
}

export interface Note {
  id: string;
  author: User;
  content: string;
  createdAt: string;
}

// date is null when the installation or maintenance date is unknown
export interface HistoryEvent {
  id: string;
  type: HistoryEventType;
  title: string;
  date: string | null;
  author: ReportAuthor | null;
  description: string | null;
  comment: string | null;
  severity: Severity | null;
  pinColor: string;
}

export interface PoleHistory {
  poleId: string;
  lifecycleYears: number | null; // null when install date is unknown
  eventCount: number;
  commentCount: number;
  events: HistoryEvent[];
}

export interface MapPole {
  id: string;
  severity: Severity;
  lat: number;
  lon: number;
}

export interface DashboardData {
  summary: DashboardSummary;
  reports: Report[];
  mapPoles: MapPole[];
  selectedReport: SelectedReport | null;
  selectedPole: PoleDetail | null;
  photos: FieldPhoto[];
  history: PoleHistory | null;
  currentUser: User;
  noteCount: number;
}

export type WsPayload =
  | { event: 'connected'; data: Record<string, unknown> }
  | { event: 'pong' }
  | { event: 'kpi_update'; data: Record<string, unknown> }
  | { event: 'report_added'; data: Record<string, unknown> }
  | { event: 'note_added'; data: { report_id: string; note: Record<string, unknown> } }
  | { event: 'report_status_changed'; data: { report_id: string; status: ReportStatus } };
