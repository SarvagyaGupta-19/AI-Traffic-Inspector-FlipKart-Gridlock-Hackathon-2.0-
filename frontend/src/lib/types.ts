/**
 * AI Traffic Inspector — TypeScript Type Definitions
 * Mirrors backend Pydantic schemas for type safety.
 */

// ─── Detection Types ────────────────────────────────────

export interface BBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface Detection {
  bbox: BBox;
  class_name: string;
  class_id: number;
  confidence: number;
  track_id?: number;
}

export interface PlateResult {
  text: string;
  confidence: number;
  bbox: BBox;
  raw_text: string;
}

// ─── Violation Types ────────────────────────────────────

export type ViolationType =
  | 'helmet_missing'
  | 'seatbelt_missing'
  | 'triple_riding'
  | 'wrong_side'
  | 'stop_line'
  | 'red_light'
  | 'illegal_parking';

export interface Violation {
  id?: number;
  type: ViolationType;
  confidence: number;
  description: string;
  detections: Detection[];
  plate?: PlateResult;
  timestamp: string;
  evidence_path?: string;
  image_path?: string;
  zone_id?: string;
}

// ─── Analysis Result ────────────────────────────────────

export interface AnalysisResult {
  image_path: string;
  detections: Detection[];
  violations: Violation[];
  plates: PlateResult[];
  processing_time_ms: number;
  frame_number?: number;
  timestamp: string;
}

// ─── API Response Types ─────────────────────────────────

export interface UploadResponse {
  success: boolean;
  message: string;
  result?: AnalysisResult;
  violations_count: number;
}

export interface ViolationRecord {
  id: number;
  type: string;
  confidence: number;
  description: string;
  plate_text?: string;
  plate_confidence?: number;
  timestamp: string;
  image_path: string;
  image_url: string;
  evidence_path: string;
  evidence_url: string;
  zone_id?: string;
  is_reviewed: boolean;
  created_at: string;
}

export interface ViolationListResponse {
  violations: ViolationRecord[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface AnalyticsResponse {
  total_violations: number;
  by_type: Record<string, number>;
  by_day: Record<string, number>;
  recent: ViolationRecord[];
  avg_confidence: number;
  plates_detected: number;
}

// ─── Zone Types ─────────────────────────────────────────

export interface ZoneConfig {
  id: string;
  name: string;
  zone_type: string;
  polygon: [number, number][];
  active: boolean;
}

// ─── Stream Types ───────────────────────────────────────

export interface StreamFrame {
  type: 'frame';
  data: string; // base64
  frame_number: number;
}

export interface StreamResult {
  type: 'result';
  frame_number: number;
  detections: Detection[];
  violations: Violation[];
  plates: PlateResult[];
  processing_time_ms: number;
  timestamp: string;
  annotated_frame?: string; // base64
}

export interface StreamControl {
  type: 'control';
  action: 'pause' | 'resume' | 'stop' | 'config';
  config?: Record<string, unknown>;
}

// ─── UI Types ───────────────────────────────────────────

export const VIOLATION_LABELS: Record<ViolationType, string> = {
  helmet_missing: 'No Helmet',
  seatbelt_missing: 'No Seatbelt',
  triple_riding: 'Triple Riding',
  wrong_side: 'Wrong Side',
  stop_line: 'Stop Line',
  red_light: 'Red Light',
  illegal_parking: 'Illegal Parking',
};

export const VIOLATION_COLORS: Record<ViolationType, string> = {
  helmet_missing: '#DE350B', // Standard Red
  seatbelt_missing: '#DE350B',
  triple_riding: '#FF991F',  // Standard Orange
  wrong_side: '#DE350B',
  stop_line: '#FF991F',
  red_light: '#DE350B',
  illegal_parking: '#403294', // Standard Purple
};

export const VIOLATION_ICONS: Record<ViolationType, string> = {
  helmet_missing: '🪖',
  seatbelt_missing: '🔗',
  triple_riding: '👥',
  wrong_side: '⛔',
  stop_line: '🛑',
  red_light: '🚦',
  illegal_parking: '🅿️',
};
