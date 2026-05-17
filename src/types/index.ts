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
  recentCriticals: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
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
  mapNode: MapPole | null;
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
  imageUrl: string | null;
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
  riskScore?: number;
  predictedSeverity?: string;
}

export interface RiskPole {
  id: string;
  lat: number;
  lon: number;
  riskScore: number;
  predictedSeverity: Severity;
  riskFactors: Record<string, unknown> | null;
  riskComputedAt: string | null;
}

export interface PredictedReport {
  id: string;
  poleId: string;
  title: string;
  predictedSeverity: Severity;
  riskScore: number;
  riskFactors: Record<string, unknown> | null;
  status: ReportStatus;
  generatedAt: string;
  lat: number;
  lon: number;
  classification: string;
  owner: string;
  circuit: string;
  address: string;
}

export interface RiskSummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
  /** Number of poles that have been scored (backend key: "scored") */
  scored: number;
  /** Unscored poles — derived from risk-poles endpoint total field */
  unscored: number;
  avgScore: number | null;
}

export interface FilterOption {
  value: string;
  label: string;
  count: number;
}

export interface DashboardFilterOptions {
  severities: FilterOption[];
  classifications: FilterOption[];
  circuits: FilterOption[];
  owners: FilterOption[];
  violationFamilies: FilterOption[];
  violationTypes: FilterOption[];
}

export interface DashboardFilterState {
  severities: Severity[];
  classifications: string[];
  circuits: string[];
  owners: string[];
  violationFamilies: string[];
  violationTypeIds: string[];
}

export interface DashboardData {
  summary: DashboardSummary;
  reports: Report[];
  mapPoles: MapPole[];
  mapPoleCount: number;
  filters: DashboardFilterOptions;
  selectedReport: SelectedReport | null;
  selectedPole: PoleDetail | null;
  photos: FieldPhoto[];
  history: PoleHistory | null;
  currentUser: User;
  noteCount: number;
}

export interface AllReportRow {
  id: string;
  poleId: string;
  title: string;
  severity: Severity;
  status: ReportStatus;
  submittedAt: string;
  location: string;
  description: string | null;
  submittedBy: ReportAuthor;
  poleLat: number;
  poleLon: number;
  poleAddress: string;
  poleClassification: string;
  poleCircuit: string;
  riskScore: number | null;
  predictedSeverity: string | null;
}

export interface AllReportsResponse {
  reports: AllReportRow[];
  total: number;
  page: number;
  pages: number;
}

export type WsPayload =
  | { event: 'connected'; data: Record<string, unknown> }
  | { event: 'pong' }
  | { event: 'kpi_update'; data: Record<string, unknown> }
  | { event: 'report_added'; data: Record<string, unknown> }
  | { event: 'note_added'; data: { report_id: string; note: Record<string, unknown> } }
  | { event: 'report_status_changed'; data: { report_id: string; status: ReportStatus } }
  | { event: 'report_severity_changed'; data: { report_id: string; pole_id: string; severity: Severity } };
