const API_KEY = import.meta.env.VITE_API_KEY || 'your-api-key-here';

const getAuthToken = (): string | null => {
  return (
    localStorage.getItem('auth_token') ||
    localStorage.getItem('access_token') ||
    localStorage.getItem('token')
  );
};

const createDefaultHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = {
    'X-API-Key': API_KEY,
  };
  const authToken = getAuthToken();
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }
  return headers;
};

interface ApiEnvelope<T> {
  data: T;
  message?: string;
}

interface ConversionStartData {
  conversion_id: string;
  filename: string;
  file_size: number;
  progress: number;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
}

interface ConversionStatusData {
  conversion_id: string;
  filename: string;
  file_size: number;
  progress: number;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  current_step?: string | null;
  message?: string | null;
  error_message?: string | null;
  result_path?: string | null;
  llm_used_model?: string | null;
  llm_attempt_count?: number;
  llm_fallback_used?: boolean;
}

export interface LargeFileRequestItem {
  request_id: string;
  requester_user_id: string;
  requester_email: string;
  request_note: string;
  bank_transfer_note: string;
  attachment_filename: string;
  attachment_size: number;
  status: string;
  created_at: string;
  updated_at: string;
  handled_by_email?: string | null;
  conversion_id?: string | null;
}

export interface LargeFileRequestFilters {
  requesterEmail?: string;
  status?: string;
  keyword?: string;
}

const parseErrorMessage = async (response: Response): Promise<string> => {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail || `요청 실패 (${response.status})`;
  } catch {
    return `요청 실패 (${response.status})`;
  }
};

export const startConversion = async (
  file: File,
  ocrEnabled: boolean
): Promise<ConversionStartData> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('ocr_enabled', String(ocrEnabled));

  const response = await fetch('/api/v1/conversion/start', {
    method: 'POST',
    headers: createDefaultHeaders(),
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const payload = (await response.json()) as ApiEnvelope<ConversionStartData>;
  return payload.data;
};

export const getConversionStatus = async (
  conversionId: string
): Promise<ConversionStatusData> => {
  const response = await fetch(
    `/api/v1/conversion/status/${encodeURIComponent(conversionId)}`,
    {
      headers: createDefaultHeaders(),
    }
  );

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const payload = (await response.json()) as ApiEnvelope<ConversionStatusData>;
  return payload.data;
};

export const createLargeFileRequest = async (
  file: File,
  requestNote: string,
  bankTransferNote: string
): Promise<LargeFileRequestItem> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('request_note', requestNote);
  formData.append('bank_transfer_note', bankTransferNote);

  const response = await fetch('/api/v1/conversion/large-file-requests', {
    method: 'POST',
    headers: createDefaultHeaders(),
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const payload = (await response.json()) as ApiEnvelope<LargeFileRequestItem>;
  return payload.data;
};

export const listLargeFileRequests = async (
  filters?: LargeFileRequestFilters
): Promise<LargeFileRequestItem[]> => {
  const params = new URLSearchParams();
  if (filters?.requesterEmail?.trim()) {
    params.set('requester_email', filters.requesterEmail.trim());
  }
  if (filters?.status?.trim()) {
    params.set('status', filters.status.trim());
  }
  if (filters?.keyword?.trim()) {
    params.set('keyword', filters.keyword.trim());
  }

  const suffix = params.toString();
  const response = await fetch(
    `/api/v1/conversion/large-file-requests${suffix ? `?${suffix}` : ''}`,
    {
    headers: createDefaultHeaders(),
    }
  );

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const payload = (await response.json()) as {
    data?: { items?: LargeFileRequestItem[] };
  };
  return payload.data?.items || [];
};

export const downloadLargeFileRequestAttachment = async (
  requestId: string,
  fallbackFilename: string
): Promise<void> => {
  const response = await fetch(
    `/api/v1/conversion/large-file-requests/${encodeURIComponent(requestId)}/attachment`,
    {
      headers: createDefaultHeaders(),
    }
  );

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = blobUrl;
  anchor.download = fallbackFilename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(blobUrl);
};

export const startLargeFileRequestConversion = async (
  requestId: string,
  file: File | null,
  ocrEnabled: boolean
): Promise<ConversionStartData> => {
  const formData = new FormData();
  formData.append('ocr_enabled', String(ocrEnabled));
  formData.append('translate_to_korean', 'false');
  if (file) {
    formData.append('file', file);
  }

  const response = await fetch(
    `/api/v1/conversion/large-file-requests/${encodeURIComponent(requestId)}/start-conversion`,
    {
      method: 'POST',
      headers: createDefaultHeaders(),
      body: formData,
    }
  );

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const payload = (await response.json()) as ApiEnvelope<ConversionStartData>;
  return payload.data;
};
