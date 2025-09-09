import { supabase } from './supabase'
export { STRIPE_PRICE_IDS } from '../constants/stripe'

export interface PaymentIntent {
  id: string
  client_secret: string
  status: string
  amount: number
  currency: string
}

export interface Subscription {
  id: string
  status: string
  current_period_end: string
  customer_id: string
  price_id: string
}

export const paymentService = {
  // 결제 의도 생성
  async createPaymentIntent(amount: number, currency: string = 'usd') {
    const { data, error } = await supabase.functions.invoke('create-payment-intent', {
      body: { amount, currency },
    })

    if (error) throw error
    return data as PaymentIntent
  },

  // 구독 생성
  async createSubscription(priceId: string) {
    const { data, error } = await supabase.functions.invoke('create-subscription', {
      body: { price_id: priceId },
    })

    if (error) throw error
    return data as { client_secret: string; subscription_id: string }
  },

  // 구독 취소
  async cancelSubscription(subscriptionId: string) {
    const { data, error } = await supabase.functions.invoke('cancel-subscription', {
      body: { subscription_id: subscriptionId },
    })

    if (error) throw error
    return data
  },

  // 사용자 구독 정보 조회
  async getUserSubscription(userId: string) {
    const { data, error } = await supabase
      .from('subscriptions')
      .select('*')
      .eq('user_id', userId)
      .single()

    if (error) throw error
    return data as Subscription
  },

  // 결제 내역 조회
  async getPaymentHistory(userId: string) {
    const { data, error } = await supabase
      .from('payments')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })

    if (error) throw error
    return data
  },

  // 환불 처리
  async processRefund(paymentIntentId: string, amount?: number) {
    const { data, error } = await supabase.functions.invoke('process-refund', {
      body: { payment_intent_id: paymentIntentId, amount },
    })

    if (error) throw error
    return data
  },

  // 웹훅 검증
  async verifyWebhook(payload: string, signature: string) {
    const { data, error } = await supabase.functions.invoke('verify-webhook', {
      body: { payload, signature },
    })

    if (error) throw error
    return data
  },
}

// Stripe 가격 ID 상수
// STRIPE_PRICE_IDS는 src/constants/stripe.ts에서 관리합니다.

// 구독 상태 상수
export const SUBSCRIPTION_STATUS = {
  ACTIVE: 'active',
  CANCELED: 'canceled',
  INCOMPLETE: 'incomplete',
  INCOMPLETE_EXPIRED: 'incomplete_expired',
  PAST_DUE: 'past_due',
  UNPAID: 'unpaid',
  PAUSED: 'paused',
}
