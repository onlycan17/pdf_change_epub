import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { useApp } from '@contexts/AppContext';
import GoogleSignInButton from '@components/auth/GoogleSignInButton';
import { buildUserFromProfile, fetchCurrentUserProfile } from '@utils/authApi';

type LoginLocationState = {
  from?:
    | string
    | {
        pathname?: string;
        search?: string;
        hash?: string;
      };
};

const resolveRedirectPath = (state: LoginLocationState | null): string => {
  const from = state?.from;
  if (typeof from === 'string' && from.trim()) {
    return from;
  }

  if (from && typeof from === 'object' && from.pathname) {
    return `${from.pathname}${from.search || ''}${from.hash || ''}`;
  }

  return '/upload';
};

const parseJsonSafely = async <T,>(response: Response): Promise<T | null> => {
  const raw = await response.text();
  if (!raw.trim()) {
    return null;
  }

  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
};

const LoginPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { dispatch } = useApp();
  const locationState = location.state as LoginLocationState | null;
  const redirectPath = resolveRedirectPath(locationState);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const body = new URLSearchParams();
      body.set('username', formData.email);
      body.set('password', formData.password);

      const response = await fetch('/api/v1/auth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
      });

      const payload = await parseJsonSafely<{ access_token?: string }>(
        response
      );

      if (!response.ok) {
        throw new Error('로그인에 실패했습니다. 계정 정보를 확인해주세요.');
      }

      if (!payload?.access_token) {
        throw new Error(
          '로그인 응답이 올바르지 않습니다. 잠시 후 다시 시도해주세요.'
        );
      }

      localStorage.setItem('auth_token', payload.access_token);
      const profile = await fetchCurrentUserProfile();
      dispatch({ type: 'SET_AUTHENTICATED', payload: true });
      dispatch({
        type: 'SET_USER',
        payload: profile ? buildUserFromProfile(profile) : null,
      });
      navigate(redirectPath, { replace: true });
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : '로그인 중 오류가 발생했습니다.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleCredential = async (credential: string) => {
    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const apiKey = import.meta.env.VITE_API_KEY || 'your-api-key-here';
      const response = await fetch('/api/v1/auth/google', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify({ id_token: credential }),
      });

      const payload = await parseJsonSafely<{
        detail?: string;
        access_token?: string;
      }>(response);

      if (!response.ok) {
        throw new Error(payload?.detail || 'Google 로그인에 실패했습니다.');
      }

      if (!payload?.access_token) {
        throw new Error(
          '로그인 서버 응답 형식이 올바르지 않습니다. 잠시 후 다시 시도해주세요.'
        );
      }

      localStorage.setItem('auth_token', payload.access_token);
      const profile = await fetchCurrentUserProfile();
      dispatch({ type: 'SET_AUTHENTICATED', payload: true });
      dispatch({
        type: 'SET_USER',
        payload: profile ? buildUserFromProfile(profile) : null,
      });
      navigate(redirectPath, { replace: true });
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'Google 로그인 중 오류가 발생했습니다.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="flex justify-center">
            <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">P2E</span>
            </div>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            로그인
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            또는{' '}
            <Link
              to="/register"
              className="font-medium text-blue-600 hover:text-blue-500"
            >
              새 계정 만들기
            </Link>
          </p>
          <p className="mt-2 text-center text-sm text-gray-600">
            무료 변환은 로그인 후 이용할 수 있습니다.
          </p>
          <p className="mt-2 text-center text-xs text-gray-500">
            데모 계정: 무료 `testuser / testpass`, 구독 `premiumuser /
            testpass`, 운영 `onlycan17@gmail.com / testpass`
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                이메일 주소
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="이메일 주소"
                value={formData.email}
                onChange={handleChange}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                비밀번호
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="비밀번호"
                value={formData.password}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label
                htmlFor="remember-me"
                className="ml-2 block text-sm text-gray-900"
              >
                로그인 상태 유지
              </label>
            </div>

            <div className="text-sm">
              <button
                type="button"
                onClick={() =>
                  setErrorMessage('비밀번호 찾기 기능은 아직 준비 중입니다.')
                }
                className="font-medium text-blue-600 hover:text-blue-500"
              >
                비밀번호를 잊으셨나요?
              </button>
            </div>
          </div>

          {errorMessage && (
            <p className="text-sm text-red-600" role="alert">
              {errorMessage}
            </p>
          )}

          <div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {isSubmitting ? '로그인 중...' : '로그인'}
            </button>
          </div>

          <div>
            <Link
              to="/"
              className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              홈으로 이동
            </Link>
          </div>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-gray-50 text-gray-500">
                  소셜 로그인
                </span>
              </div>
            </div>

            <div className="mt-6">
              <GoogleSignInButton
                onCredential={handleGoogleCredential}
                disabled={isSubmitting}
              />
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
