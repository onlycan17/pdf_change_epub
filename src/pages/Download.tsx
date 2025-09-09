import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Button } from '../components/common'
import {
  Download as DownloadIcon,
  FileText,
  Clock,
  Share2,
  RefreshCw,
  CheckCircle,
} from 'lucide-react'

const Download: React.FC = () => {
  const { user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const isPremium = user?.is_premium || false

  const { file, options, downloadUrl, fileSize, conversionTime } = location.state || {}

  if (!file || !downloadUrl) {
    navigate('/upload')
    return null
  }

  const handleDownload = () => {
    // TODO: 실제 파일 다운로드 로직 구현
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = file.name.replace('.pdf', '.epub')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleConvertAnother = () => {
    navigate('/upload')
  }

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'PDF to EPUB 변환 완료',
          text: `변환된 EPUB 파일: ${file.name.replace('.pdf', '.epub')}`,
          url: window.location.href,
        })
      } catch (error) {
        // 공유 취소됨
      }
    } else {
      // 클립보드에 복사
      navigator.clipboard.writeText(window.location.href)
      alert('링크가 클립보드에 복사되었습니다.')
    }
  }

  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000)
    if (seconds < 60) return `${seconds}초`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}분 ${remainingSeconds}초`
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <button
              onClick={handleConvertAnother}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              ← 다른 파일 변환
            </button>
            <h1 className="text-2xl font-bold text-gray-900">변환 완료</h1>
            <div className="flex items-center space-x-4">
              {isPremium && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                  프리미엄
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* 성공 메시지 */}
        <div className="text-center mb-12">
          <div className="bg-green-50 border border-green-200 rounded-lg p-8 mb-8">
            <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
            <h2 className="text-3xl font-bold text-green-800 mb-2">변환 완료!</h2>
            <p className="text-green-700">PDF 파일이 성공적으로 EPUB로 변환되었습니다.</p>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* 파일 정보 */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">파일 정보</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">원본 파일</span>
                <span className="font-medium">{file.name}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">변환된 파일</span>
                <span className="font-medium">{file.name.replace('.pdf', '.epub')}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">파일 크기</span>
                <span className="font-medium">{formatFileSize(fileSize)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">변환 시간</span>
                <span className="font-medium flex items-center">
                  <Clock className="w-4 h-4 mr-1" />
                  {formatTime(conversionTime)}
                </span>
              </div>
            </div>
          </div>

          {/* 변환 옵션 */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">적용된 옵션</h3>
            <div className="space-y-3">
              {options.ocr && (
                <div className="flex items-center text-green-600">
                  <div className="w-2 h-2 bg-green-600 rounded-full mr-3"></div>
                  <span>OCR 텍스트 인식</span>
                </div>
              )}
              {options.llm && (
                <div className="flex items-center text-green-600">
                  <div className="w-2 h-2 bg-green-600 rounded-full mr-3"></div>
                  <span>AI 문맥 개선</span>
                </div>
              )}
              {options.highQualityImages && (
                <div className="flex items-center text-green-600">
                  <div className="w-2 h-2 bg-green-600 rounded-full mr-3"></div>
                  <span>고해상도 이미지</span>
                </div>
              )}
              {!options.ocr && !options.llm && !options.highQualityImages && (
                <p className="text-gray-500">기본 변환 옵션 사용</p>
              )}
            </div>
          </div>
        </div>

        {/* 다운로드 버튼 */}
        <div className="text-center mt-12">
          <Button onClick={handleDownload} variant="primary" size="lg" className="px-8 mb-4">
            <DownloadIcon className="w-5 h-5 mr-2" />
            EPUB 파일 다운로드
          </Button>

          <p className="text-sm text-gray-500 mb-8">다운로드 링크는 24시간 동안 유효합니다.</p>
        </div>

        {/* 추가 작업 */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">추가 작업</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Button onClick={handleConvertAnother} variant="secondary" className="w-full">
              <RefreshCw className="w-4 h-4 mr-2" />
              다른 파일 변환
            </Button>

            <Button onClick={handleShare} variant="secondary" className="w-full">
              <Share2 className="w-4 h-4 mr-2" />
              공유하기
            </Button>

            <Button onClick={() => navigate('/')} variant="secondary" className="w-full">
              <FileText className="w-4 h-4 mr-2" />
              홈으로 돌아가기
            </Button>
          </div>
        </div>

        {/* 광고 (무료 사용자만) */}
        {!isPremium && (
          <div className="mt-8 bg-gray-100 rounded-lg p-6 text-center">
            <p className="text-gray-600 mb-4">광고</p>
            <div className="bg-white rounded p-8 border-2 border-dashed border-gray-300">
              <p className="text-gray-500">Google AdSense 광고가 표시됩니다</p>
            </div>
            <p className="text-sm text-gray-500 mt-4">
              광고를 제거하고 더 나은 경험을 원하신다면 프리미엄으로 업그레이드하세요.
            </p>
          </div>
        )}

        {/* 프리미엄 사용자 안내 */}
        {isPremium && (
          <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-yellow-600 rounded-full flex items-center justify-center mr-3">
                <span className="text-white font-bold text-sm">P</span>
              </div>
              <h3 className="text-lg font-semibold text-yellow-800">프리미엄 혜택</h3>
            </div>
            <p className="text-yellow-700">
              프리미엄 회원님, 감사합니다! 광고 없는 깔끔한 환경과 우선 순위 처리를 이용하고
              계십니다. 계속해서 최고의 변환 경험을 누려보세요.
            </p>
          </div>
        )}
      </main>
    </div>
  )
}

export default Download
