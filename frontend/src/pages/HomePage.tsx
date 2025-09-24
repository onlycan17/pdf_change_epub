import React from 'react'
import { Link } from 'react-router-dom'

const HomePage: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto">
      {/* Hero Section */}
      <section className="text-center py-16">
        <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
          PDF를 EPUB으로
          <span className="text-blue-600 block">간편하게 변환</span>
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
          AI 기술을 활용한 고품질 PDF to EPUB 변환 서비스. 
          텍스트 추출, 레이아웃 보존, 다양한 언어 지원으로 완벽한 전자책을 만들어보세요.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/upload"
            className="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            무료로 시작하기
          </Link>
          <Link
            to="/premium"
            className="border border-blue-600 text-blue-600 px-8 py-3 rounded-lg font-medium hover:bg-blue-50 transition-colors"
          >
            프리미엄 기능 보기
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">왜 우리 서비스를 선택하나요?</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            최신 AI 기술과 사용자 친화적인 인터페이스로 완벽한 변환 경험을 제공합니다.
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center p-6">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">고품질 변환</h3>
            <p className="text-gray-600">
              AI 기반 텍스트 인식으로 원본의 레이아웃과 서식을 최대한 보존합니다.
            </p>
          </div>

          <div className="text-center p-6">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">빠른 처리 속도</h3>
            <p className="text-gray-600">
              클라우드 기반 분산 처리로 대용량 파일도 빠르게 변환합니다.
            </p>
          </div>

          <div className="text-center p-6">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">안전한 보안</h3>
            <p className="text-gray-600">
              업로드된 파일은 암호화되어 안전하게 보관되며, 변환 후 자동 삭제됩니다.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-blue-600 rounded-2xl p-8 md:p-12 text-center text-white">
        <h2 className="text-3xl font-bold mb-4">지금 바로 시작해보세요</h2>
        <p className="text-blue-100 mb-6 max-w-2xl mx-auto">
          무료 계정으로 매월 5개의 PDF를 EPUB으로 변환할 수 있습니다. 
          프리미엄으로 업그레이드하면 제한 없이 사용 가능합니다.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/upload"
            className="bg-white text-blue-600 px-8 py-3 rounded-lg font-medium hover:bg-blue-50 transition-colors"
          >
            무료 변환 시작
          </Link>
          <Link
            to="/premium"
            className="border border-white text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            프리미엄 알아보기
          </Link>
        </div>
      </section>
    </div>
  )
}

export default HomePage