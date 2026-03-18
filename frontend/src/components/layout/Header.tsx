import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useApp } from '@contexts/AppContext';
import {
  buildUserFromProfile,
  fetchCurrentUserProfile,
  logoutCurrentSession,
} from '@utils/authApi';

const Header: React.FC = () => {
  const { state, dispatch } = useApp();
  const location = useLocation();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isPrivileged, setIsPrivileged] = useState(false);

  useEffect(() => {
    const run = async () => {
      const profile = await fetchCurrentUserProfile();
      setIsPrivileged(Boolean(profile?.is_privileged));
      dispatch({
        type: 'SET_USER',
        payload: profile ? buildUserFromProfile(profile) : null,
      });
      if (!profile) {
        dispatch({ type: 'SET_AUTHENTICATED', payload: false });
      }
    };
    void run();
  }, [dispatch, state.isAuthenticated]);

  useEffect(() => {
    setIsMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    document.body.style.overflow = isMenuOpen ? 'hidden' : '';

    return () => {
      document.body.style.overflow = '';
    };
  }, [isMenuOpen]);

  const handleLogout = async () => {
    await logoutCurrentSession();
    dispatch({ type: 'SET_USER', payload: null });
    dispatch({ type: 'SET_AUTHENTICATED', payload: false });
    setIsPrivileged(false);
    setIsMenuOpen(false);
    navigate('/login', { replace: true });
  };

  const navigation = [
    { name: '홈', href: '/' },
    { name: '변환하기', href: '/upload' },
    ...(isPrivileged
      ? [{ name: '운영대시보드', href: '/admin/dashboard' }]
      : []),
    {
      name: isPrivileged ? '요청관리' : '대용량 요청',
      href: isPrivileged ? '/large-file-requests' : '/large-file-request',
    },
    { name: '후원', href: '/support' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="sticky top-0 z-40 bg-white/95 shadow-sm border-b border-gray-200 backdrop-blur">
      <nav className="mx-auto w-full max-w-7xl px-4 py-3 sm:px-6 sm:py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 sm:gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600">
              <span className="text-white font-bold text-sm">P2E</span>
            </div>
            <div className="min-w-0">
              <span className="block text-base font-bold leading-tight text-gray-900 sm:text-xl">
                PDF to EPUB
              </span>
              <span className="hidden text-xs text-gray-500 sm:block">
                작은 화면에서도 읽기 쉬운 전자책 변환
              </span>
            </div>
          </Link>

          <div className="hidden md:flex items-center space-x-8">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive(item.href)
                    ? 'text-blue-600 bg-blue-50'
                    : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                }`}
              >
                {item.name}
              </Link>
            ))}
          </div>

          <div className="hidden md:flex items-center space-x-4">
            {state.isAuthenticated ? (
              <>
                <Link
                  to="/profile"
                  className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
                >
                  프로필
                </Link>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
                >
                  로그아웃
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
                >
                  로그인
                </Link>
                <Link
                  to="/register"
                  className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
                >
                  회원가입
                </Link>
              </>
            )}
          </div>

          <button
            type="button"
            className="touch-target md:hidden inline-flex items-center justify-center rounded-lg border border-gray-200 px-3 text-sm font-medium text-gray-700 transition hover:border-blue-200 hover:text-blue-600 hover:bg-blue-50"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-expanded={isMenuOpen}
            aria-controls="mobile-navigation"
            aria-label={isMenuOpen ? '메뉴 닫기' : '메뉴 열기'}
          >
            <span className="mr-2">{isMenuOpen ? '닫기' : '메뉴'}</span>
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <title>{isMenuOpen ? '메뉴 닫기' : '메뉴 열기'}</title>
              {isMenuOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>

        {isMenuOpen && (
          <div className="md:hidden">
            <button
              type="button"
              className="fixed inset-0 top-[61px] z-40 bg-slate-950/20 backdrop-blur-[1px]"
              aria-label="메뉴 닫기"
              onClick={() => setIsMenuOpen(false)}
            />
            <div
              id="mobile-navigation"
              className="animate-fade-in absolute inset-x-4 top-full z-50 mt-3 overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 shadow-xl"
            >
              <div className="space-y-2">
                {navigation.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`touch-target flex items-center rounded-xl px-4 py-3 text-base font-medium transition-colors ${
                      isActive(item.href)
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-blue-600'
                    }`}
                    onClick={() => setIsMenuOpen(false)}
                  >
                    {item.name}
                  </Link>
                ))}
              </div>
              <div className="mt-4 border-t border-gray-200 pt-4 space-y-2">
                {state.isAuthenticated ? (
                  <>
                    <Link
                      to="/profile"
                      className="touch-target flex items-center rounded-xl px-4 py-3 text-base font-medium text-gray-700 hover:bg-gray-50 hover:text-blue-600"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      프로필
                    </Link>
                    <button
                      type="button"
                      onClick={handleLogout}
                      className="touch-target flex w-full items-center rounded-xl px-4 py-3 text-left text-base font-medium text-gray-700 hover:bg-gray-50 hover:text-blue-600"
                    >
                      로그아웃
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      to="/login"
                      className="touch-target flex items-center rounded-xl px-4 py-3 text-base font-medium text-gray-700 hover:bg-gray-50 hover:text-blue-600"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      로그인
                    </Link>
                    <Link
                      to="/register"
                      className="touch-target flex items-center justify-center rounded-xl bg-blue-600 px-4 py-3 text-base font-medium text-white hover:bg-blue-700"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      회원가입
                    </Link>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
};

export default Header;
