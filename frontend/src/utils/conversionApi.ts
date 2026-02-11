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
