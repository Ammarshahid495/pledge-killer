/**
 * Pledge Fighter API Client.
 */

const API_BASE = 'https://pledge-killer.onrender.com/api/v1';

export interface User {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
}

export interface Classroom {
  id: string;
  title: string;
  description?: string;
  language: string;
  status: string;
  min_submissions: number;
  deadline?: string;
  max_participants?: number;
  created_at: string;
  participant_count: number;
  valid_submission_count: number;
  threshold_met: boolean;
  my_anonymous_label?: string;
  join_token?: string;
  join_url?: string;
  has_submitted?: boolean;
  my_submission_id?: string;
  has_report?: boolean;
  my_report_id?: string;
}

export interface SubmissionVersion {
  id: string;
  version_number: number;
  sha256_hash: string;
  file_size: number;
  original_filename: string;
  language: string;
  processing_status: string;
  created_at: string;
}

export interface Submission {
  id: string;
  classroom_id: string;
  status: string;
  current_version?: SubmissionVersion;
  submitted_at: string;
  updated_at: string;
  raw_code?: string;
}

export interface FunctionMatchDetail {
  function_name: string;
  peer_function_name: string;
  my_start_line: number;
  my_end_line: number;
  peer_start_line: number;
  peer_end_line: number;
  similarity_percentage: number;
  matched_tokens: number;
  total_function_tokens: number;
  match_type: 'EXACT' | 'LOGICAL';
  verdict: string;
}

export interface MatchRegion {
  my_start_line: number;
  my_end_line: number;
  peer_start_line?: number;
  peer_end_line?: number;
  matched_token_count: number;
  region_score: number;
  match_type?: 'EXACT' | 'LOGICAL';
  function_name?: string;
  peer_function_name?: string;
}

export interface MatchDetail {
  match_id: string;
  peer_label: string;
  similarity_score: number;
  directional_coverage_to_peer: number;
  directional_coverage_from_peer: number;
  shared_fingerprint_count: number;
  matched_token_count: number;
  regions: MatchRegion[];
  matched_functions?: FunctionMatchDetail[];
  explanation: string;
}

export interface ReportDetail {
  report_id: string;
  classroom_id: string;
  classroom_title: string;
  submission_id: string;
  report_version: number;
  status: string;
  highest_similarity: number;
  comparisons_count: number;
  total_matching_regions: number;
  generated_at: string;
  engine_version: string;
  my_source_code: string;
  matches: MatchDetail[];
  all_regions: MatchRegion[];
}

export interface ReportSummary {
  report_id: string;
  classroom_id: string;
  classroom_title: string;
  submission_id: string;
  report_version: number;
  status: string;
  highest_similarity: number;
  comparisons_count: number;
  total_matching_regions: number;
  generated_at: string;
  engine_version: string;
}

const FIELD_LABELS: Record<string, string> = {
  display_name: 'Name',
  email: 'Email',
  password: 'Password',
  confirm_password: 'Confirm password',
  deadline: 'Deadline',
  title: 'Title',
  token: 'Reset link',
};

/**
 * Turns any error body into one readable sentence.
 * FastAPI sends HTTPException as {detail: {code, message}} and validation
 * errors (422) as {detail: [{loc, msg}, ...]}; the app's own handler uses
 * {error: {message}}.
 */
function extractErrorMessage(data: any, status: number): string {
  const detail = data?.detail;
  if (typeof detail === 'string' && detail) return detail;
  if (detail && !Array.isArray(detail) && detail.message) return detail.message;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((d: any) => {
        const field = Array.isArray(d.loc) ? String(d.loc[d.loc.length - 1]) : '';
        const msg = String(d.msg || 'Invalid value').replace(/^Value error, /, '');
        if (/field required/i.test(msg) && field) {
          return `${FIELD_LABELS[field] || field} is required`;
        }
        return msg;
      })
      .join('. ');
  }
  if (data?.error?.message) return data.error.message;
  if (data?.message) return data.message;
  if (status >= 500) return 'Something went wrong on the server. Please try again in a moment.';
  return 'Request failed. Please try again.';
}

class ApiClient {
  private token: string | null = localStorage.getItem('access_token');

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers || {});
    if (this.token) {
      headers.set('Authorization', `Bearer ${this.token}`);
    }

    if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    let response: Response;
    try {
      response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
      });
    } catch {
      throw new Error('Cannot reach the server. Check your internet connection and try again.');
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok || !data.success) {
      throw new Error(extractErrorMessage(data, response.status));
    }

    return data.data;
  }

  // Auth
  async register(body: any): Promise<User> {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async login(body: any): Promise<{ access_token: string; refresh_token: string; user_id: string; display_name: string; email: string }> {
    const data = await this.request<any>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(body),
    });
    this.setToken(data.access_token);
    return data;
  }

  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.setToken(null);
    }
  }

  async getMe(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  async forgotPassword(email: string): Promise<{ email_sent: boolean }> {
    return this.request<{ email_sent: boolean }>('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  async resetPassword(token: string, password: string, confirmPassword: string): Promise<void> {
    await this.request('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, password, confirm_password: confirmPassword }),
    });
  }

  // Classrooms
  async createClassroom(body: { title: string; description?: string; min_submissions?: number; deadline: string; max_participants?: number }): Promise<Classroom> {
    return this.request<Classroom>('/classrooms', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async getClassrooms(): Promise<Classroom[]> {
    return this.request<Classroom[]>('/classrooms');
  }

  async getClassroom(id: string): Promise<Classroom> {
    return this.request<Classroom>(`/classrooms/${id}`);
  }

  async joinClassroom(token: string): Promise<Classroom> {
    const clean = token.trim();
    return this.request<Classroom>(`/classrooms/join/${encodeURIComponent(clean)}`, {
      method: 'POST',
    });
  }

  async getMembers(classroomId: string): Promise<Array<{ anonymous_label: string; joined_at: string; status: string }>> {
    return this.request(`/classrooms/${classroomId}/members`);
  }

  // Submissions
  async uploadSubmission(classroomId: string, file: File): Promise<Submission> {
    const formData = new FormData();
    formData.append('file', file);
    return this.request<Submission>(`/classrooms/${classroomId}/submissions`, {
      method: 'POST',
      body: formData,
    });
  }

  async getMySubmission(classroomId: string): Promise<Submission> {
    return this.request<Submission>(`/classrooms/${classroomId}/submissions/me`);
  }

  async deleteMySubmission(classroomId: string): Promise<void> {
    await this.request(`/classrooms/${classroomId}/submissions/me`, {
      method: 'DELETE',
    });
  }

  // Reports
  async getMyReports(): Promise<ReportSummary[]> {
    return this.request<ReportSummary[]>('/reports/me');
  }

  async getReportDetail(reportId: string): Promise<ReportDetail> {
    return this.request<ReportDetail>(`/reports/me/${reportId}`);
  }

  /**
   * Download the report as a JSON file. The endpoint returns raw JSON (not the
   * {success, data} envelope) and requires the Authorization header, so it
   * cannot go through request() or window.open().
   */
  async downloadReportJSON(reportId: string): Promise<void> {
    const headers = new Headers();
    if (this.token) {
      headers.set('Authorization', `Bearer ${this.token}`);
    }

    const response = await fetch(`${API_BASE}/reports/me/${reportId}/download`, { headers });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail?.message || err.error?.message || 'Failed to download report');
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report_${reportId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

export const api = new ApiClient();
