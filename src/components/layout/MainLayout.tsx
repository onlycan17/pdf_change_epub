import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { supabaseService } from '../../services/supabase'
import Header from './Header'
import DesktopSidebar from './DesktopSidebar'
import '../../styles/responsive.css'
import '../../styles/design-system.css'

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
      // 로그아웃 실패 처리
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Mobile Header - Only show on mobile/tablet */}
      <div className="lg:hidden">
        <Header />
      </div>

      <div className="lg:flex lg:h-screen">
        {/* Desktop Sidebar - Only show on desktop */}
        <DesktopSidebar onLogout={handleLogout} />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Desktop Header - Only show on desktop */}
          <div className="hidden lg:block lg:flex-shrink-0">
            <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                    {document.title || 'PDF to EPUB 변환기'}
                  </h1>
                </div>

                {/* Desktop User Info & Actions */}
                <div className="flex items-center space-x-4">
                  {user && user.is_premium && (
                    <div className="flex items-center space-x-2 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 px-3 py-1 rounded-full text-sm font-medium">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      <span>프리미엄</span>
                    </div>
                  )}

                  {user && (
                    <div className="text-sm text-gray-600 dark:text-gray-400">{user.email}</div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <main className="flex-1 relative overflow-y-auto focus:outline-none">
            <div className="lg:container lg:mx-auto lg:px-6 lg:py-8">{children}</div>
          </main>
        </div>
      </div>
    </div>
  )
}

export default MainLayout
