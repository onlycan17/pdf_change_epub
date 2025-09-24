import React from 'react'

const ConvertPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">변환 진행 중</h1>
        <p className="text-gray-600">
          PDF 파일이 EPUB으로 변환되고 있습니다. 잠시만 기다려주세요.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center">
          <div className="w-24 h-24 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-12 h-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </div>
          
          <h2 className="text-xl font-semibold text-gray-900 mb-2">document.pdf 변환 중</h2>
          <p className="text-gray-600 mb-6">파일 크기: 2.4MB</p>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
            <div className="bg-blue-600 h-2 rounded-full" style={{ width: '45%' }}></div>
          </div>
          
          <p className="text-sm text-gray-500 mb-2">45% 완료</p>
          <p className="text-sm text-gray-500">예상 남은 시간: 약 2분 30초</p>

          <div className="mt-8 space-y-4">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">텍스트 추출</span>
              <span className="text-green-600">완료</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">이미지 처리</span>
              <span className="text-blue-600">진행 중</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">EPUB 생성</span>
              <span className="text-gray-400">대기 중</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConvertPage