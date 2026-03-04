import { getAuthToken } from '@utils/subscription';

const API_KEY = import.meta.env.VITE_API_KEY || 'your-api-key-here';

export interface CurrentUserProfile {
  id: string;
  email: string;
}

export const fetchCurrentUserProfile = async (): Promise<CurrentUserProfile | null> => {
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

export const isPrivilegedEmail = (email: string | null | undefined): boolean => {
  return (email || '').trim().toLowerCase() === 'onlycan17@gmail.com';
};
