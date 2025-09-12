import React, { useState } from 'react'
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
  Crown,
  ArrowLeft,
  Copy,
} from 'lucide-react'

const Download: React.FC = () => {
  const { user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const isPremium = user?.is_premium || false
  const [copied, setCopied] = useState(false)

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
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100 dark:from-slate-900 dark:to-slate-800">
      {/* 헤더 */}
      <header className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md border-b border-gray-200/50 dark:border-slate-700/50 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <button
              onClick={handleConvertAnother}
              className="flex items-center px-4 py-2 text-blue-600 hover:text-blue-700 font-medium transition-all rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              다른 파일 변환
            </button>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">변환 완료</h1>
            <div className="flex items-center space-x-4">
              {isPremium && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gradient-to-r from-yellow-400 to-orange-500 text-white shadow-lg">
                  <Crown className="w-4 h-4 mr-1" />
                  프리미엄
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* 성공 메시지 */}
        <div className="text-center mb-12">
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200 dark:border-green-800 rounded-2xl p-8 mb-8 shadow-lg">
            <div className="w-20 h-20 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
              <CheckCircle className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-4xl font-bold text-green-800 dark:text-green-300 mb-3">
              변환 완료!
            </h2>
            <p className="text-lg text-green-700 dark:text-green-400">
              PDF 파일이 성공적으로 EPUB로 변환되었습니다.
            </p>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 mb-12">
          {/* 파일 정보 */}
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-8">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-6 flex items-center">
              <FileText className="w-5 h-5 mr-2 text-blue-500" />
              파일 정보
            </h3>
            <div className="space-y-6">
              <div className="flex justify-between items-center pb-4 border-b border-gray-100 dark:border-slate-700">
                <span className="text-sm text-gray-500 dark:text-slate-400">원본 파일</span>
                <span className="font-medium text-gray-700 dark:text-slate-300 truncate max-w-[140px]">
                  {file.name}
                </span>
              </div>
              <div className="flex justify-between items-center pb-4 border-b border-gray-100 dark:border-slate-700">
                <span className="text-sm text-gray-500 dark:text-slate-400">변환된 파일</span>
                <span className="font-medium text-gray-700 dark:text-slate-300 truncate max-w-[140px]">
                  {file.name.replace('.pdf', '.epub')}
                </span>
              </div>
              <div className="flex justify-between items-center pb-4 border-b border-gray-100 dark:border-slate-700">
                <span className="text-sm text-gray-500 dark:text-slate-400">파일 크기</span>
                <span className="font-medium text-gray-700 dark:text-slate-300">
                  {formatFileSize(fileSize)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500 dark:text-slate-400">변환 시간</span>
                <span className="font-medium text-gray-700 dark:text-slate-300 flex items-center">
                  <Clock className="w-4 h-4 mr-2" />
                  {formatTime(conversionTime)}
                </span>
              </div>
            </div>
          </div>

          {/* 변환 옵션 */}
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-8">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-6 flex items-center">
              <Crown className="w-5 h-5 mr-2 text-blue-500" />
              적용된 옵션
            </h3>
            <div className="space-y-4">
              {options.ocr && (
                <div className="flex items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-4"></div>
                  <span className="text-green-700 dark:text-green-400">OCR 텍스트 인식</span>
                </div>
              )}
              {options.llm && (
                <div className="flex items-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="w-3 h-3 bg-blue-500 rounded-full mr-4"></div>
                  <span className="text-blue-700 dark:text-blue-400">AI 문맥 개선</span>
                </div>
              )}
              {options.highQualityImages && (
                <div className="flex items-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                  <div className="w-3 h-3 bg-purple-500 rounded-full mr-4"></div>
                  <span className="text-purple-700 dark:text-purple-400">고해상도 이미지</span>
                </div>
              )}
              {!options.ocr && !options.llm && !options.highQualityImages && (
                <div className="flex items-center p-3 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
                  <div className="w-3 h-3 bg-gray-400 rounded-full mr-4"></div>
                  <span className="text-gray-600 dark:text-slate-400">기본 변환 옵션 사용</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 다운로드 버튼 */}
        <div className="text-center mb-12">
          <Button
            onClick={handleDownload}
            variant="primary"
            size="lg"
            className="px-10 py-4 text-lg mb-6 shadow-lg hover:shadow-xl transition-all duration-300"
          >
            <DownloadIcon className="w-6 h-6 mr-3" />
            EPUB 파일 다운로드
          </Button>

          <p className="text-sm text-gray-500 dark:text-slate-400 mb-8">
            다운로드 링크는 24시간 동안 유효합니다.
          </p>
        </div>

        {/* 추가 작업 */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-8 mb-12">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">추가 작업</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Button
              onClick={handleConvertAnother}
              variant="secondary"
              className="w-full py-3 px-4 flex items-center justify-center"
            >
              <RefreshCw className="w-5 h-5 mr-2" />
              다른 파일 변환
            </Button>

            <Button
              onClick={handleShare}
              variant="secondary"
              className="w-full py-3 px-4 flex items-center justify-center"
            >
              <Share2 className="w-5 h-5 mr-2" />
              공유하기
            </Button>

            <Button
              onClick={() => navigator.clipboard.writeText(window.location.href)}
              variant="secondary"
              className="w-full py-3 px-4 flex items-center justify-center"
            >
              <Copy className="w-5 h-5 mr-2" />
              {copied ? '복사됨!' : '링크 복사'}
            </Button>

            <Button
              onClick={() => navigate('/')}
              variant="secondary"
              className="w-full py-3 px-4 flex items-center justify-center"
            >
              <FileText className="w-5 h-5 mr-2" />
              홈으로 돌아가기
            </Button>
          </div>
        </div>

        {/* 광고 (무료 사용자만) */}
        {!isPremium && (
          <div className="bg-gradient-to-r from-gray-100 to-slate-200 dark:from-slate-700 dark:to-slate-800 rounded-xl p-8 text-center border border-gray-200 dark:border-slate-700 shadow-lg mb-12">
            <div className="flex items-center justify-between mb-6">
              <p className="text-sm text-gray-600 dark:text-slate-400">광고</p>
              <button
                onClick={() => navigate('/premium')}
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline font-medium"
              >
                광고 제거하기
              </button>
            </div>
            <div className="bg-white dark:bg-slate-600 rounded-lg p-8 border-2 border-dashed border-gray-300 dark:border-slate-500">
              <p className="text-gray-500 dark:text-slate-400">Google AdSense 광고가 표시됩니다</p>
            </div>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-6">
              광고를 제거하고 더 나은 경험을 원하신다면 프리미엄으로 업그레이드하세요.
            </p>
          </div>
        )}

        {/* 프리미엄 사용자 안내 */}
        {isPremium && (
          <div className="bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-8 shadow-lg">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-gradient-to-r from-yellow-500 to-orange-600 rounded-full flex items-center justify-center mr-4 shadow-lg">
                <Crown className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-yellow-800 dark:text-yellow-300">
                프리미엄 혜택
              </h3>
            </div>
            <p className="text-yellow-700 dark:text-yellow-400">
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
