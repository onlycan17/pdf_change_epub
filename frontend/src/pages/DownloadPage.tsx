import React from 'react'
import { Link } from 'react-router-dom'

const DownloadPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">변환 완료</h1>
        <p className="text-gray-600">
          PDF 파일이 성공적으로 EPUB으로 변환되었습니다.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center">
          <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-12 h-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          
          <h2 className="text-xl font-semibold text-gray-900 mb-2">document.epub</h2>
          <p className="text-gray-600 mb-6">파일 크기: 1.8MB · 변환 시간: 3분 15초</p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <button className="bg-blue-600 text-white px-6 py-3 rounded-md font-medium hover:bg-blue-700 transition-colors">
              EPUB 파일 다운로드
            </button>
            <button className="border border-gray-300 text-gray-700 px-6 py-3 rounded-md font-medium hover:bg-gray-50 transition-colors">
              이메일로 보내기
            </button>
          </div>

          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h3 className="font-semibold text-gray-900 mb-2">변환 정보</h3>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">원본 파일:</span>
                <span className="ml-2 text-gray-900">document.pdf (2.4MB)</span>
              </div>
              <div>
                <span className="text-gray-600">변환된 파일:</span>
                <span className="ml-2 text-gray-900">document.epub (1.8MB)</span>
              </div>
              <div>
                <span className="text-gray-600">변환 품질:</span>
                <span className="ml-2 text-gray-900">고품질</span>
              </div>
              <div>
                <span className="text-gray-600">변환 시간:</span>
                <span className="ml-2 text-gray-900">3분 15초</span>
              </div>
            </div>
          </div>

          <div className="flex justify-center space-x-4">
            <Link
              to="/upload"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              다른 파일 변환하기
            </Link>
            <span className="text-gray-300">|</span>
            <Link
              to="/premium"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              프리미엄으로 업그레이드
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DownloadPage