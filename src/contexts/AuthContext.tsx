import React, { createContext, useCallback, useEffect, useState } from 'react'
import { supabase, supabaseService } from '../services/supabase'
import { logger } from '../utils/logger'

interface User {
  id: string
  email: string
  is_premium: boolean
  created_at: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  signIn: () => Promise<void>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Context providers are exempt from fast refresh rule
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchUserData = async (userId: string) => {
    try {
      // Fetch user data from your users table
      const { data, error } = await supabase.from('users').select('*').eq('id', userId).single()

      if (error) throw error
      if (data) {
        setUser(data)
      }
    } catch (error) {
      logger.error('Error fetching user data:', error)
    } finally {
      setLoading(false)
    }
  }

  const checkUser = useCallback(async () => {
    try {
      const {
        data: { user: authUser },
      } = await supabase.auth.getUser()
      if (authUser) {
        await fetchUserData(authUser.id)
      } else {
        setLoading(false)
      }
    } catch (error) {
      logger.error('Error checking user:', error)
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // Check active sessions and sets the user
    checkUser()

    // Listen for changes on auth state (logged in, signed out, etc.)
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        // Fetch additional user data from database
        fetchUserData(session.user.id)
      } else {
        setUser(null)
        setLoading(false)
      }
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [checkUser])

  const signIn = async () => {
    await supabaseService.signInWithGoogle()
  }

  const signOut = async () => {
    await supabaseService.signOut()
    setUser(null)
  }

  const value = {
    user,
    loading,
    signIn,
    signOut,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
