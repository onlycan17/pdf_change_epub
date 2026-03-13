const API_KEY = import.meta.env.VITE_API_KEY || 'your-api-key-here';

const getAuthToken = (): string | null => {
  return (
    localStorage.getItem('auth_token') ||
    localStorage.getItem('access_token') ||
    localStorage.getItem('token')
  );
};

const createHeaders = (): HeadersInit => {
  const headers: Record<string, string> = {
    'X-API-Key': API_KEY,
  };
  const token = getAuthToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
};

const parseErrorMessage = async (response: Response): Promise<string> => {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail || `요청 실패 (${response.status})`;
  } catch {
    return `요청 실패 (${response.status})`;
  }
};

export interface AdminDashboardSummary {
  total_users: number;
  local_users: number;
  google_users: number;
  today_free_conversions: number;
  total_large_file_requests: number;
  pending_large_file_requests: number;
  processing_large_file_requests: number;
  runtime_pending_jobs: number;
  runtime_processing_jobs: number;
  runtime_completed_jobs: number;
  runtime_failed_jobs: number;
  persisted_total_conversions: number;
  persisted_failed_conversions: number;
  persisted_completed_conversions: number;
}

export interface AdminDashboardDailyUsageItem {
  date: string;
  count: number;
}

export interface AdminDashboardLargeFileRequestItem {
  request_id: string;
  requester_email: string;
  attachment_filename: string;
  attachment_size: number;
  status: string;
  created_at: string;
  updated_at: string;
  handled_by_email?: string | null;
}

export interface AdminDashboardConversionItem {
  conversion_id: string;
  filename: string;
  file_size: number;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  created_at: string;
  updated_at: string;
  current_step?: string | null;
  error_message?: string | null;
}

export interface AdminDashboardFailureCategoryItem {
  code: string;
  label: string;
  count: number;
}

export interface AdminDashboardData {
  summary: AdminDashboardSummary;
  daily_free_usage: AdminDashboardDailyUsageItem[];
  daily_conversion_counts: AdminDashboardDailyUsageItem[];
  recent_large_file_requests: AdminDashboardLargeFileRequestItem[];
  recent_runtime_conversions: AdminDashboardConversionItem[];
  recent_failed_conversions: AdminDashboardConversionItem[];
  failure_category_counts: AdminDashboardFailureCategoryItem[];
}

export const fetchAdminDashboard = async (): Promise<AdminDashboardData> => {
  const response = await fetch('/api/v1/admin/dashboard', {
    headers: createHeaders(),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const payload = (await response.json()) as { data: AdminDashboardData };
  return payload.data;
};
