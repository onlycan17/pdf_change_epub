import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { useApp } from '@contexts/AppContext';
import GoogleSignInButton from '@components/auth/GoogleSignInButton';

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

      const payload = await parseJsonSafely<{ access_token?: string }>(response);

      if (!response.ok) {
        throw new Error('로그인에 실패했습니다. 계정 정보를 확인해주세요.');
      }

      if (!payload?.access_token) {
        throw new Error('로그인 응답이 올바르지 않습니다. 잠시 후 다시 시도해주세요.');
      }

      localStorage.setItem('auth_token', payload.access_token);
      dispatch({ type: 'SET_AUTHENTICATED', payload: true });
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
      dispatch({ type: 'SET_AUTHENTICATED', payload: true });
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

            <div className="mt-6 grid grid-cols-2 gap-3">
              <GoogleSignInButton
                onCredential={handleGoogleCredential}
                disabled={isSubmitting}
              />

              <button
                type="button"
                className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
              >
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <title>GitHub 로그인</title>
                  <path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.174-.105-.949-.199-2.403.042-3.441.219-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.094.113.108.212.08.326-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.402.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.357-.629-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24.009 12.017 24.009c6.624 0 11.99-5.367 11.99-11.988C24.007 5.367 18.641.001.012.001z" />
                </svg>
                <span className="ml-2">GitHub</span>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
