import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { supabaseService } from '../../services/supabase'
import DarkModeToggle from '../common/DarkModeToggle'
import { Menu, X, User, Crown, LogOut, Settings, FileText } from 'lucide-react'

const Header: React.FC = () => {
  const { user, loading } = useAuth()
  const navigate = useNavigate()
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)

  const handleLogout = async () => {
    try {
      await supabaseService.signOut()
      navigate('/login')
    } catch (error) {
      // console.error('로그아웃 실패:', error)
    }
  }

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen)
  }

  const toggleUserMenu = () => {
    setIsUserMenuOpen(!isUserMenuOpen)
  }

  if (loading) {
    return (
      <header className="bg-white dark:bg-gray-900 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="animate-pulse h-8 w-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
            </div>
            <div className="animate-pulse h-8 w-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        </div>
      </header>
    )
  }

  return (
    <header className="bg-white dark:bg-gray-900 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <FileText className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">PDF to EPUB</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">변환기</p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            <Link
              to="/"
              className="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 px-3 py-2 rounded-md text-sm font-medium transition-colors"
            >
              홈
            </Link>
            <Link
              to="/upload"
              className="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 px-3 py-2 rounded-md text-sm font-medium transition-colors"
            >
              변환하기
            </Link>
            <Link
              to="/premium"
              className="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 px-3 py-2 rounded-md text-sm font-medium transition-colors"
            >
              프리미엄
            </Link>
          </nav>

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            {/* Dark Mode Toggle */}
            <DarkModeToggle />

            {user ? (
              <>
                {/* Premium Badge */}
                {user.is_premium && (
                  <div className="hidden sm:flex items-center space-x-1 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 px-2 py-1 rounded-full text-xs font-medium">
                    <Crown className="w-3 h-3" />
                    <span>프리미엄</span>
                  </div>
                )}

                {/* User Menu Dropdown */}
                <div className="relative">
                  <button
                    onClick={toggleUserMenu}
                    className="flex items-center space-x-2 text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 p-2 rounded-lg transition-colors"
                  >
                    <User className="h-5 w-5" />
                    <span className="hidden sm:block text-sm font-medium">
                      {user.email?.split('@')[0]}
                    </span>
                  </button>

                  {isUserMenuOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 z-50 border border-gray-200 dark:border-gray-700">
                      <Link
                        to="/settings"
                        className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        <Settings className="w-4 h-4 mr-2" />
                        설정
                      </Link>
                      <button
                        onClick={handleLogout}
                        className="flex items-center w-full px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        <LogOut className="w-4 h-4 mr-2" />
                        로그아웃
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                {/* 무료 사용자를 위한 로그인 유도 */}
                <Link
                  to="/premium"
                  className="hidden sm:inline-flex items-center text-sm text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                >
                  <Crown className="w-4 h-4 mr-1" />
                  프리미엄
                </Link>
                <Link
                  to="/login"
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  로그인
                </Link>
              </>
            )}

            {/* Mobile menu button */}
            <button
              onClick={toggleMenu}
              className="md:hidden p-2 rounded-md text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden border-t border-gray-200 dark:border-gray-700">
            <div className="px-2 pt-2 pb-3 space-y-1">
              <Link
                to="/"
                className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                홈
              </Link>
              <Link
                to="/upload"
                className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                변환하기
              </Link>
              <Link
                to="/premium"
                className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                프리미엄
              </Link>
              {user && (
                <>
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-2">
                    <div className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">
                      {user.email}
                    </div>
                    <button
                      onClick={() => {
                        handleLogout()
                        setIsMenuOpen(false)
                      }}
                      className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    >
                      로그아웃
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  )
}

export default Header
