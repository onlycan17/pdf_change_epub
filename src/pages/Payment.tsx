import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { useAuth } from '../hooks/useAuth'
import { Button } from '../components/common'
import { paymentService, STRIPE_PRICE_IDS } from '../services/payment'
import { supabaseService } from '../services/supabase'
import { CreditCard, Shield, CheckCircle, AlertCircle } from 'lucide-react'

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY)

interface PaymentFormProps {
  onSuccess: () => void
  onError: (error: string) => void
}

const PaymentForm: React.FC<PaymentFormProps> = ({ onSuccess, onError }) => {
  const stripe = useStripe()
  const elements = useElements()
  const { user } = useAuth()
  const [isProcessing, setIsProcessing] = useState(false)
  const [cardComplete, setCardComplete] = useState(false)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()

    if (!stripe || !elements) {
      return
    }

    if (!cardComplete) {
      onError('카드 정보를 완성해주세요.')
      return
    }

    setIsProcessing(true)

    try {
      // 구독 생성
      const subscription = await paymentService.createSubscription(STRIPE_PRICE_IDS.PREMIUM_MONTHLY)

      const { error, paymentIntent } = await stripe.confirmCardPayment(subscription.client_secret, {
        payment_method: {
          card: elements.getElement(CardElement)!,
          billing_details: {
            name: user?.email || '사용자',
          },
        },
      })

      if (error) {
        onError(error.message || '결제 처리 중 오류가 발생했습니다.')
      } else if (paymentIntent && paymentIntent.status === 'succeeded') {
        // 사용자 정보 업데이트 (프리미엄 상태 활성화)
        if (user?.id) {
          await supabaseService.updateUserPremiumStatus(user.id, true)
        }
        onSuccess()
      }
    } catch (error) {
      // console.error('결제 처리 실패:', error)
      onError('결제 처리 중 오류가 발생했습니다.')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">결제 정보 입력</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">카드 정보</label>
            <div className="border border-gray-300 rounded-lg p-4">
              <CardElement
                onChange={event => {
                  setCardComplete(event.complete)
                }}
                options={{
                  style: {
                    base: {
                      fontSize: '16px',
                      color: '#424770',
                      '::placeholder': {
                        color: '#aab7c4',
                      },
                    },
                    invalid: {
                      color: '#9e2146',
                    },
                  },
                }}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center">
          <Shield className="w-5 h-5 text-blue-600 mr-2" />
          <p className="text-sm text-blue-800">결제 정보는 Stripe를 통해 안전하게 처리됩니다.</p>
        </div>
      </div>

      <Button
        type="submit"
        disabled={!stripe || isProcessing || !cardComplete}
        isLoading={isProcessing}
        variant="primary"
        className="w-full"
      >
        <CreditCard className="w-4 h-4 mr-2" />
        {isProcessing ? '결제 처리 중...' : '결제하기'}
      </Button>
    </form>
  )
}

const Payment: React.FC = () => {
  const navigate = useNavigate()
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'processing' | 'success' | 'error'>(
    'idle'
  )
  const [errorMessage, setErrorMessage] = useState('')

  const handlePaymentSuccess = () => {
    setPaymentStatus('success')
    // 3초 후 홈으로 이동
    setTimeout(() => {
      navigate('/')
    }, 3000)
  }

  const handlePaymentError = (error: string) => {
    setErrorMessage(error)
    setPaymentStatus('error')
  }

  const handleRetry = () => {
    setPaymentStatus('idle')
    setErrorMessage('')
  }

  if (paymentStatus === 'success') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">결제 완료!</h2>
            <p className="text-gray-600 mb-6">프리미엄 플랜이 성공적으로 활성화되었습니다.</p>
            <p className="text-sm text-gray-500">3초 후 홈으로 이동합니다...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <button
              onClick={() => navigate('/premium')}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              ← 뒤로가기
            </button>
            <h1 className="text-2xl font-bold text-gray-900">결제</h1>
            <div></div>
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* 결제 정보 */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">결제 정보</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">플랜</span>
              <span className="font-medium">프리미엄 월간 구독</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">가격</span>
              <span className="font-medium">$9.99/월</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">다음 결제일</span>
              <span className="font-medium">
                {new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString('ko-KR')}
              </span>
            </div>
          </div>
        </div>

        {/* 에러 메시지 */}
        {paymentStatus === 'error' && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
              <div>
                <h3 className="text-lg font-semibold text-red-800">결제 실패</h3>
                <p className="text-red-700">{errorMessage}</p>
              </div>
            </div>
            <Button onClick={handleRetry} variant="secondary" className="mt-4">
              다시 시도
            </Button>
          </div>
        )}

        {/* 결제 폼 */}
        <Elements stripe={stripePromise}>
          <PaymentForm onSuccess={handlePaymentSuccess} onError={handlePaymentError} />
        </Elements>

        {/* 약관 */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            결제함으로써{' '}
            <a href="/terms" className="text-blue-600 hover:underline">
              이용약관
            </a>
            및{' '}
            <a href="/privacy" className="text-blue-600 hover:underline">
              개인정보처리방침
            </a>
            에 동의합니다.
          </p>
        </div>
      </main>
    </div>
  )
}

export default Payment
