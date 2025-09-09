import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { useAuth } from './hooks/useAuth'
import MainLayout from './components/layout/MainLayout'
import Home from './pages/Home'
import Login from './pages/Login'
import AuthCallback from './pages/AuthCallback'
import FileUpload from './pages/FileUpload'
import Premium from './pages/Premium'
import ConversionProgress from './pages/ConversionProgress'
import Download from './pages/Download'
import Error from './pages/Error'
import Payment from './pages/Payment'
import './App.css'

// Protected Route Component (for premium features)
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return user ? <>{children}</> : <Navigate to="/login" replace />
}

// Public Route Component (redirects to home if authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return user ? <Navigate to="/" replace /> : <>{children}</>
}

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public routes without layout */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/auth/callback"
        element={
          <PublicRoute>
            <AuthCallback />
          </PublicRoute>
        }
      />

      {/* Routes with main layout */}
      <Route
        path="/*"
        element={
          <MainLayout>
            <Routes>
              {/* Public routes (무료 기능) */}
              <Route path="/" element={<Home />} />
              <Route path="/upload" element={<FileUpload />} />
              <Route path="/convert" element={<ConversionProgress />} />
              <Route path="/download" element={<Download />} />
              <Route path="/premium" element={<Premium />} />
              <Route path="/error" element={<Error />} />

              {/* Protected routes (프리미엄 기능) */}
              <Route
                path="/payment"
                element={
                  <ProtectedRoute>
                    <Payment />
                  </ProtectedRoute>
                }
              />

              {/* Catch all route */}
              <Route path="*" element={<Navigate to="/error" replace />} />
            </Routes>
          </MainLayout>
        }
      />
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <Router>
          <AppRoutes />
        </Router>
      </ThemeProvider>
    </AuthProvider>
  )
}

export default App
