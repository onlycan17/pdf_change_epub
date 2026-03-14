import type { User } from '@/types';
import { clearAuthTokens, getCurrentPlan } from '@utils/subscription';

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

const buildDisplayName = (email: string): string => {
  const localPart = email.split('@')[0]?.trim() || '사용자';
  const normalized = localPart.replace(/[._-]+/g, ' ').trim();
  if (!normalized) {
    return '사용자';
  }
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
};

export const fetchCurrentUserProfile =
  async (): Promise<CurrentUserProfile | null> => {
    const headers: Record<string, string> = {
      'X-API-Key': API_KEY,
    };

    const response = await fetch('/api/v1/auth/me', {
      credentials: 'same-origin',
      headers,
    });

    if (!response.ok) {
      clearAuthTokens();
      return null;
    }

    const payload = (await response.json()) as CurrentUserProfile;
    if (!payload.email || !payload.id) {
      return null;
    }

    return payload;
  };

export const buildUserFromProfile = (profile: CurrentUserProfile): User => {
  const currentPlan = getCurrentPlan();
  return {
    id: profile.id,
    email: profile.email,
    name: buildDisplayName(profile.email),
    isPremium: currentPlan.isSubscribed,
  };
};

export const clearSession = (): void => {
  clearAuthTokens();
};

export const logoutCurrentSession = async (): Promise<void> => {
  const headers: Record<string, string> = {
    'X-API-Key': API_KEY,
  };

  try {
    await fetch('/api/v1/auth/logout', {
      method: 'POST',
      credentials: 'same-origin',
      headers,
    });
  } finally {
    clearAuthTokens();
  }
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
