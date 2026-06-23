/**
 * AI Traffic Inspector — API Client
 * Communicates with the FastAPI backend.
 */
import type {
  UploadResponse,
  ViolationRecord,
  ViolationListResponse,
  AnalyticsResponse,
  ZoneConfig,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('gridlock_token');
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      ...options.headers as Record<string, string>,
    };

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'API request failed');
    }

    return response.json();
  }

  // ─── Upload ───────────────────────────────────────────────

  async uploadImage(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<UploadResponse>('/api/upload', {
      method: 'POST',
      body: formData,
    });
  }

  // ─── Violations ───────────────────────────────────────────

  async getViolations(params?: {
    page?: number;
    per_page?: number;
    type?: string;
    plate?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<ViolationListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.per_page) searchParams.set('per_page', String(params.per_page));
    if (params?.type) searchParams.set('type', params.type);
    if (params?.plate) searchParams.set('plate', params.plate);
    if (params?.status) searchParams.set('status', params.status);
    if (params?.start_date) searchParams.set('start_date', params.start_date);
    if (params?.end_date) searchParams.set('end_date', params.end_date);

    const query = searchParams.toString();
    return this.request<ViolationListResponse>(
      `/api/violations${query ? `?${query}` : ''}`
    );
  }

  async getViolation(id: number): Promise<ViolationRecord> {
    return this.request<ViolationRecord>(`/api/violations/${id}`);
  }

  async deleteViolation(id: number): Promise<{ success: boolean }> {
    return this.request(`/api/violations/${id}`, { method: 'DELETE' });
  }

  async updateViolationStatus(id: number, status: 'pending' | 'issued' | 'rejected'): Promise<{ success: boolean }> {
    return this.request(`/api/violations/${id}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
  }

  // ─── Analytics ────────────────────────────────────────────

  async getAnalytics(): Promise<AnalyticsResponse> {
    return this.request<AnalyticsResponse>('/api/analytics');
  }

  // ─── Zones ────────────────────────────────────────────────

  async getZones(): Promise<{ zones: ZoneConfig[] }> {
    return this.request('/api/zones');
  }

  async createZone(zone: ZoneConfig): Promise<{ success: boolean; zone: ZoneConfig }> {
    return this.request('/api/zones', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(zone),
    });
  }

  async deleteZone(id: string): Promise<{ success: boolean }> {
    return this.request(`/api/zones/${id}`, { method: 'DELETE' });
  }

  // --- System ---
  async healthCheck(): Promise<{ status: string }> {
    return this.request('/api/health');
  }

  async getModelInfo(): Promise<Record<string, unknown>> {
    return this.request('/api/model-info');
  }

  async resetDatabase(): Promise<{ success: boolean; cleared: number; message: string }> {
    return this.request('/api/reset', { method: 'POST' });
  }

  // --- Video Upload (SSE streaming) ---

  /**
   * Upload a video and get an SSE stream of frame-by-frame results.
   * Returns the fetch Response for manual SSE parsing.
   */
  async uploadVideoStream(file: File, frameSkip: number = 3, locationStr: string = ''): Promise<Response> {
    const formData = new FormData();
    formData.append('file', file);
    if (locationStr) {
      formData.append('location', locationStr);
    }

    const url = `${this.baseUrl}/api/upload-video?frame_skip=${frameSkip}`;
    const headers: Record<string, string> = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const res = await fetch(url, {
      method: 'POST',
      body: formData,
      headers,
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`Video upload failed (${res.status}): ${errorText}`);
    }

    return res;
  }

  // --- Helpers ---

  getEvidenceUrl(filename: string): string {
    if (!filename) return '';
    return `${this.baseUrl}/api/evidence/${filename}`;
  }

  getUploadUrl(filename: string): string {
    if (!filename) return '';
    return `${this.baseUrl}/api/uploads/${filename}`;
  }

  getWebSocketUrl(): string {
    const wsBase = this.baseUrl.replace(/^http/, 'ws');
    return `${wsBase}/ws/stream`;
  }
}

export const api = new ApiClient();
export default api;

