import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { supabaseService } from '../../services/supabase'
import DesktopSidebar from './DesktopSidebar'
import '../../styles/modern-desktop.css'

interface MainLayoutProps {
  children: React.ReactNode
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { user } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      await supabaseService.signOut()
      navigate('/login')
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('로그아웃 실패:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
      {/* Desktop Header - Enhanced for desktop */}
      <header className="bg-white/80 dark:bg-slate-800/80 backdrop-blur border-b border-slate-200 dark:border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Title */}
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/')}
                className="flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
              >
                <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                  />
                </svg>
                홈으로
              </button>
              <div className="hidden lg:block">
                <h1 className="text-xl font-semibold text-slate-900 dark:text-white">
                  PDF to EPUB 변환기
                </h1>
              </div>
            </div>

            {/* Desktop User Info & Actions - Enhanced */}
            <div className="flex items-center space-x-4">
              {!user ? (
                <button onClick={() => navigate('/login')} className="btn btn-primary btn-sm">
                  로그인
                </button>
              ) : (
                <div className="flex items-center space-x-3">
                  {user.is_premium && (
                    <div className="badge badge-premium flex items-center space-x-1">
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      <span>프리미엄</span>
                    </div>
                  )}

                  <div className="text-sm text-slate-600 dark:text-slate-400 hidden sm:block">
                    {user.email}
                  </div>

                  <button onClick={handleLogout} className="btn btn-ghost btn-sm">
                    로그아웃
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Desktop Sidebar - Enhanced for desktop */}
        <DesktopSidebar onLogout={handleLogout} />

        {/* Main Content Area - Enhanced for desktop */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Main Content */}
          <main className="flex-1 relative overflow-y-auto focus:outline-none">
            <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-8">{children}</div>
          </main>

          {/* Enhanced Footer */}
          <footer className="bg-white/80 dark:bg-slate-800/80 backdrop-blur border-t border-slate-200 dark:border-slate-700">
            <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-6">
              <div className="flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0">
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  © 2024 PDF to EPUB 변환기. All rights reserved.
                </div>
                <div className="flex items-center space-x-6 text-sm">
                  <a
                    href="#"
                    className="text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                  >
                    이용약관
                  </a>
                  <a
                    href="#"
                    className="text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                  >
                    개인정보처리방침
                  </a>
                  <a
                    href="#"
                    className="text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                  >
                    고객센터
                  </a>
                </div>
              </div>
            </div>
          </footer>
        </div>
      </div>
    </div>
  )
}

export default MainLayout
