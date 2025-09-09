import { createClient } from '@supabase/supabase-js'
import type { ConversionStatus } from '../constants/status'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// 데이터베이스 타입 정의
export interface User {
  id: string
  email: string
  is_premium: boolean
  created_at: string
}

export interface Conversion {
  id: string
  user_id: string
  filename: string
  file_size: number
  status: ConversionStatus
  created_at: string
  updated_at?: string
  error_message?: string
}

// Supabase 클라이언트 함수들
export const supabaseService = {
  // 사용자 관련 함수들
  async getCurrentUser() {
    const {
      data: { user },
    } = await supabase.auth.getUser()
    return user
  },

  async signInWithGoogle() {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    return { data, error }
  },

  async signOut() {
    const { error } = await supabase.auth.signOut()
    return { error }
  },

  // 변환 기록 관련 함수들
  async createConversion(conversion: Omit<Conversion, 'id' | 'created_at'>) {
    const { data, error } = await supabase.from('conversions').insert(conversion).select().single()
    return { data, error }
  },

  async getUserConversions(userId: string) {
    const { data, error } = await supabase
      .from('conversions')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .limit(10)
    return { data, error }
  },

  async updateConversionStatus(id: string, status: Conversion['status'], errorMessage?: string) {
    const updateData: Partial<Conversion> = {
      status,
      updated_at: new Date().toISOString(),
    }
    if (errorMessage) {
      updateData.error_message = errorMessage
    }

    const { data, error } = await supabase
      .from('conversions')
      .update(updateData)
      .eq('id', id)
      .select()
      .single()
    return { data, error }
  },

  // 사용자 프리미엄 상태 업데이트
  async updateUserPremiumStatus(userId: string, isPremium: boolean) {
    const { data, error } = await supabase
      .from('users')
      .update({ is_premium: isPremium })
      .eq('id', userId)
      .select()
      .single()
    return { data, error }
  },
}
