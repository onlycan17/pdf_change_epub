import { getAuthToken } from '@utils/subscription';

const API_KEY = import.meta.env.VITE_API_KEY || 'your-api-key-here';

export interface CurrentUserProfile {
  id: string;
  email: string;
  is_privileged: boolean;
}

export interface RegisterUserInput {
  name: string;
  email: string;
  password: string;
}

export const fetchCurrentUserProfile =
  async (): Promise<CurrentUserProfile | null> => {
    const token = getAuthToken();
    if (!token) {
      return null;
    }

    const response = await fetch('/api/v1/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-API-Key': API_KEY,
      },
    });

    if (!response.ok) {
      return null;
    }

    const payload = (await response.json()) as CurrentUserProfile;
    if (!payload.email || !payload.id) {
      return null;
    }

    return payload;
  };

export const isPrivilegedEmail = (
  email: string | null | undefined
): boolean => {
  return (email || '').trim().toLowerCase() === 'onlycan17@gmail.com';
};

export const registerUser = async ({
  name,
  email,
  password,
}: RegisterUserInput): Promise<void> => {
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    },
    body: JSON.stringify({
      name,
      email,
      password,
    }),
  });

  const payload = (await response.json().catch(() => null)) as {
    detail?: string;
  } | null;

  if (!response.ok) {
    throw new Error(payload?.detail || '회원가입에 실패했습니다.');
  }
};
