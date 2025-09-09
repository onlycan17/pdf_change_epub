import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { Home, Upload, Crown, User, LogOut, FileText } from 'lucide-react'

interface DesktopSidebarProps {
  onLogout: () => void
}

const DesktopSidebar: React.FC<DesktopSidebarProps> = ({ onLogout }) => {
  const { user } = useAuth()
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Convert', href: '/upload', icon: Upload },
    { name: 'Premium', href: '/premium', icon: Crown },
  ]

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="hidden lg:flex lg:flex-shrink-0">
      <div className="flex flex-col w-72">
        {/* Sidebar component */}
        <div className="flex flex-col h-0 flex-1 bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800 border-r border-slate-200 dark:border-slate-700">
          {/* Logo Header */}
          <div className="flex-shrink-0 px-6 py-8 border-b border-slate-200 dark:border-slate-700">
            <Link to="/" className="flex items-center space-x-3 group">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-all duration-300">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 dark:from-white dark:to-slate-300 bg-clip-text text-transparent">
                  PDF to EPUB
                </h1>
                <p className="text-xs text-slate-500 dark:text-slate-400">AI Converter</p>
              </div>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="mt-8 flex-1 px-4 space-y-2">
            {navigation.map(item => {
              const Icon = item.icon
              const active = isActive(item.href)

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`
                    group flex items-center px-4 py-3 text-sm font-medium rounded-2xl transition-all duration-200
                    ${
                      active
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/25'
                        : 'text-slate-600 dark:text-slate-300 hover:bg-white/50 dark:hover:bg-slate-800/50 hover:text-slate-900 dark:hover:text-white'
                    }
                  `}
                >
                  <div
                    className={`
                    w-10 h-10 rounded-xl flex items-center justify-center mr-3 transition-all duration-200
                    ${
                      active
                        ? 'bg-white/20 backdrop-blur'
                        : 'bg-slate-100 dark:bg-slate-800 group-hover:bg-blue-100 dark:group-hover:bg-blue-900/30'
                    }
                  `}
                  >
                    <Icon
                      className={`w-5 h-5 ${active ? 'text-white' : 'text-slate-500 dark:text-slate-400 group-hover:text-blue-600'}`}
                    />
                  </div>
                  {item.name}

                  {active && (
                    <div className="ml-auto">
                      <div className="w-2 h-2 bg-white rounded-full"></div>
                    </div>
                  )}
                </Link>
              )
            })}
          </nav>

          {/* User Section */}
          {user && (
            <div className="flex-shrink-0 border-t border-slate-200 dark:border-slate-700 p-4">
              <div className="bg-white/50 dark:bg-slate-800/50 backdrop-blur rounded-2xl p-4 border border-slate-200 dark:border-slate-700">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-10 h-10 bg-gradient-to-br from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-600 rounded-xl flex items-center justify-center">
                    <User className="w-5 h-5 text-slate-600 dark:text-slate-300" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                      {user.email?.split('@')[0]}
                    </p>
                    {user.is_premium && (
                      <div className="flex items-center gap-1">
                        <Crown className="w-3 h-3 text-yellow-500" />
                        <span className="text-xs text-yellow-600 dark:text-yellow-400 font-medium">
                          Premium
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <button
                  onClick={onLogout}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-slate-600 dark:text-slate-300 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all duration-200"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DesktopSidebar
