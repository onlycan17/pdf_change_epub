import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Button } from '../components/common'
import { Check, Crown, Star, ArrowRight } from 'lucide-react'

const Premium: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const isPremium = user?.is_premium || false

  const features = [
    {
      category: '파일 처리',
      items: [
        { text: '최대 300MB 파일 지원', premium: true },
        { text: '고급 OCR 텍스트 인식', premium: true },
        { text: 'AI 문맥 개선 (DeepSeek)', premium: true },
        { text: '고해상도 이미지 처리', premium: true },
        { text: '최대 10MB 파일 지원', premium: false },
        { text: '기본 텍스트 추출', premium: false },
      ],
    },
    {
      category: '사용자 경험',
      items: [
        { text: '광고 없는 깔끔한 환경', premium: true },
        { text: '우선 순위 변환 처리', premium: true },
        { text: '무제한 LLM 사용', premium: true },
        { text: '고급 설정 옵션', premium: true },
        { text: '일일 5회 LLM 사용 제한', premium: false },
        { text: '기본 변환 옵션', premium: false },
      ],
    },
    {
      category: '지원',
      items: [
        { text: '우선 고객 지원', premium: true },
        { text: '상세 변환 리포트', premium: true },
        { text: '일괄 변환 기능', premium: true },
        { text: 'API 액세스', premium: true },
        { text: '기본 고객 지원', premium: false },
        { text: '표준 변환 리포트', premium: false },
      ],
    },
  ]

  const handleUpgrade = () => {
    navigate('/payment')
  }

  if (isPremium) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <button
                onClick={() => navigate('/')}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                ← 홈으로
              </button>
              <h1 className="text-2xl font-bold text-gray-900">프리미엄 플랜</h1>
              <div></div>
            </div>
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 mb-8">
              <Crown className="w-16 h-16 text-yellow-600 mx-auto mb-4" />
              <h2 className="text-3xl font-bold text-yellow-800 mb-2">이미 프리미엄 회원입니다!</h2>
              <p className="text-yellow-700 mb-6">
                현재 프리미엄 플랜을 이용 중입니다. 모든 고급 기능을 자유롭게 사용하실 수 있습니다.
              </p>
              <Button onClick={() => navigate('/')} variant="primary">
                변환 시작하기
              </Button>
            </div>
          </div>
        </main>
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
              onClick={() => navigate('/')}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              ← 홈으로
            </button>
            <h1 className="text-2xl font-bold text-gray-900">프리미엄 플랜</h1>
            <div></div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* 히어로 섹션 */}
        <div className="text-center mb-16">
          <Crown className="w-16 h-16 text-yellow-600 mx-auto mb-4" />
          <h2 className="text-4xl font-bold text-gray-900 mb-4">프리미엄으로 업그레이드하세요</h2>
          <p className="text-xl text-gray-600 mb-8">
            고급 기능을 모두 이용하고 최고의 PDF to EPUB 변환 경험을 만드세요
          </p>

          {/* 가격 카드 */}
          <div className="bg-white rounded-lg shadow-lg p-8 max-w-md mx-auto">
            <div className="text-center">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">프리미엄 플랜</h3>
              <div className="mb-4">
                <span className="text-5xl font-bold text-gray-900">$9.99</span>
                <span className="text-gray-600">/월</span>
              </div>
              <p className="text-gray-600 mb-6">월간 구독 • 언제든지 취소 가능</p>

              <Button onClick={handleUpgrade} variant="premium" size="lg" className="w-full mb-4">
                프리미엄 시작하기
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>

              <p className="text-xs text-gray-500">
                7일 무료 체험 후 $9.99/월 • 언제든지 취소 가능
              </p>
            </div>
          </div>
        </div>

        {/* 기능 비교 */}
        <div className="mb-16">
          <h3 className="text-3xl font-bold text-center text-gray-900 mb-12">플랜 비교</h3>

          <div className="grid gap-8">
            {features.map((category, categoryIndex) => (
              <div key={categoryIndex} className="bg-white rounded-lg shadow-sm overflow-hidden">
                <div className="px-6 py-4 bg-gray-50 border-b">
                  <h4 className="text-lg font-semibold text-gray-900">{category.category}</h4>
                </div>
                <div className="divide-y divide-gray-200">
                  {category.items.map((item, itemIndex) => (
                    <div
                      key={itemIndex}
                      className={`px-6 py-4 flex items-center justify-between ${
                        item.premium ? 'bg-yellow-50' : ''
                      }`}
                    >
                      <span
                        className={`text-sm ${item.premium ? 'text-gray-900' : 'text-gray-600'}`}
                      >
                        {item.text}
                      </span>
                      {item.premium ? (
                        <Star className="w-5 h-5 text-yellow-500" />
                      ) : (
                        <Check className="w-5 h-5 text-green-500" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 자주 묻는 질문 */}
        <div className="mb-16">
          <h3 className="text-3xl font-bold text-center text-gray-900 mb-12">자주 묻는 질문</h3>

          <div className="space-y-4 max-w-3xl mx-auto">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h4 className="font-semibold text-gray-900 mb-2">무료 체험은 어떻게 하나요?</h4>
              <p className="text-gray-600">
                프리미엄 플랜에 가입하시면 7일간 무료로 이용하실 수 있습니다. 체험 기간 중에는
                언제든지 취소 가능하며, 요금이 청구되지 않습니다.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h4 className="font-semibold text-gray-900 mb-2">언제든지 취소할 수 있나요?</h4>
              <p className="text-gray-600">
                네, 언제든지 구독을 취소할 수 있습니다. 취소 후에는 현재 결제 주기가 끝날 때까지
                프리미엄 기능을 계속 이용하실 수 있습니다.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h4 className="font-semibold text-gray-900 mb-2">OCR이란 무엇인가요?</h4>
              <p className="text-gray-600">
                OCR(광학 문자 인식)은 스캔된 문서나 이미지에서 텍스트를 자동으로 인식하는
                기술입니다. 프리미엄 플랜에서는 고급 OCR 기능을 통해 스캔본 PDF의 텍스트를 정확하게
                추출합니다.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h4 className="font-semibold text-gray-900 mb-2">
                AI 문맥 개선은 어떻게 작동하나요?
              </h4>
              <p className="text-gray-600">
                DeepSeek AI를 활용하여 문단 간의 문맥을 분석하고 자연스러운 연결을 만듭니다. 특히
                표나 복잡한 레이아웃이 있는 문서에서 개선된 결과를 제공합니다.
              </p>
            </div>
          </div>
        </div>

        {/* CTA 섹션 */}
        <div className="text-center bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-white">
          <h3 className="text-2xl font-bold mb-4">지금 시작하세요</h3>
          <p className="text-lg mb-6 opacity-90">
            7일 무료 체험으로 프리미엄 기능을 직접 경험해보세요
          </p>
          <Button
            onClick={handleUpgrade}
            variant="premium"
            size="lg"
            className="bg-white text-purple-600 hover:bg-gray-100"
          >
            무료 체험 시작하기
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </main>
    </div>
  )
}

export default Premium
