import React from 'react'
import { Link } from 'react-router-dom'

const PremiumPage: React.FC = () => {
  const features = [
    '무제한 PDF 변환',
    '대용량 파일 지원 (최대 500MB)',
    '고급 OCR 기능',
    '배치 처리 (한 번에 여러 파일)',
    '우선 순위 처리',
    '이메일 알림',
    '클라우드 저장소 연동',
    '전문가 지원'
  ]

  const plans = [
    {
      name: '무료',
      price: '₩0',
      period: '영구 무료',
      description: '기본적인 변환 기능',
      features: ['월 5회 변환', '최대 100MB 파일', '기본 OCR', '표준 처리'],
      buttonText: '현재 사용 중',
      buttonVariant: 'outline'
    },
    {
      name: '프리미엄',
      price: '₩9,900',
      period: '월',
      description: '전체 기능 사용',
      features: ['무제한 변환', '최대 500MB 파일', '고급 OCR', '우선 처리', '배치 처리', '이메일 알림'],
      buttonText: '구독하기',
      buttonVariant: 'primary',
      popular: true
    },
    {
      name: '연간',
      price: '₩99,000',
      period: '년',
      description: '2개월 무료 할인',
      features: ['무제한 변환', '최대 500MB 파일', '고급 OCR', '우선 처리', '배치 처리', '이메일 알림', '클라우드 연동'],
      buttonText: '구독하기',
      buttonVariant: 'outline'
    }
  ]

  return (
    <div className="max-w-7xl mx-auto">
      {/* Hero Section */}
      <section className="text-center py-16">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">프리미엄으로 더 많은 기능을 이용하세요</h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          무제한 변환, 대용량 파일 지원, 고급 기능들을 통해 더 나은 경험을 누려보세요.
        </p>
      </section>

      {/* Pricing Plans */}
      <section className="py-16">
        <div className="grid md:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`bg-white rounded-2xl shadow-sm border ${
                plan.popular ? 'border-blue-500 ring-2 ring-blue-500' : 'border-gray-200'
              } p-8 relative`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                    가장 인기 있는
                  </span>
                </div>
              )}
              
              <div className="text-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                <div className="flex items-baseline justify-center mb-2">
                  <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                  <span className="text-gray-600 ml-2">/{plan.period}</span>
                </div>
                <p className="text-gray-600">{plan.description}</p>
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-center">
                    <svg className="w-5 h-5 text-green-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                className={`w-full py-3 rounded-lg font-medium transition-colors ${
                  plan.buttonVariant === 'primary'
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {plan.buttonText}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Feature Comparison */}
      <section className="py-16 bg-gray-50 rounded-2xl">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">기능 비교</h2>
          <p className="text-gray-600">무료와 프리미엄의 차이를 확인해보세요</p>
        </div>

        <div className="max-w-4xl mx-auto">
          <table className="w-full bg-white rounded-lg shadow-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left p-4 font-semibold text-gray-900">기능</th>
                <th className="text-center p-4 font-semibold text-gray-900">무료</th>
                <th className="text-center p-4 font-semibold text-blue-600">프리미엄</th>
              </tr>
            </thead>
            <tbody>
              {features.map((feature, index) => (
                <tr key={index} className="border-b border-gray-100">
                  <td className="p-4 text-gray-700">{feature}</td>
                  <td className="p-4 text-center">
                    {index > 2 ? (
                      <span className="text-gray-400">-</span>
                    ) : (
                      <svg className="w-5 h-5 text-green-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </td>
                  <td className="p-4 text-center">
                    <svg className="w-5 h-5 text-green-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">아직도 고민되시나요?</h2>
        <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
          7일 무료 체험으로 프리미엄 기능을 직접 경험해보세요. 만족하지 않으시면 언제든지 취소 가능합니다.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/upload"
            className="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            7일 무료 체험 시작
          </Link>
          <Link
            to="/"
            className="border border-gray-300 text-gray-700 px-8 py-3 rounded-lg font-medium hover:bg-gray-50 transition-colors"
          >
            더 알아보기
          </Link>
        </div>
      </section>
    </div>
  )
}

export default PremiumPage