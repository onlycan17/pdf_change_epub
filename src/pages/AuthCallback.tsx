import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../services/supabase'

const AuthCallback: React.FC = () => {
  const navigate = useNavigate()

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Get the session from the URL
        const { data, error } = await supabase.auth.getSession()

        if (error) {
          // TODO: Add proper error handling and logging
          // console.error('Auth callback error:', error)
          navigate('/login?error=auth_failed')
          return
        }

        if (data.session) {
          // Successfully authenticated
          // The AuthContext will handle the user data fetching
          navigate('/')
        } else {
          // No session found
          navigate('/login?error=no_session')
        }
      } catch (error) {
        // TODO: Add proper error handling and logging
        // console.error('Unexpected error in auth callback:', error)
        navigate('/login?error=unexpected')
      }
    }

    handleAuthCallback()
  }, [navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">로그인 처리 중...</h2>
        <p className="text-gray-600">잠시만 기다려 주세요.</p>
      </div>
    </div>
  )
}

export default AuthCallback
