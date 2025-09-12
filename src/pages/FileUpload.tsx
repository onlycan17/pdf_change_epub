import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { FileUpload as FileUploadComponent, Button } from '../components/common'
import { Crown, FileText, Image, Brain, Upload, Zap, Shield } from 'lucide-react'

const FileUpload: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [selectedOptions, setSelectedOptions] = useState({
    ocr: false,
    llm: false,
    highQualityImages: false,
  })

  const isPremium = user?.is_premium || false
  const maxFileSize = isPremium ? 300 : 10 // MB

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
  }

  const handleOptionChange = (option: keyof typeof selectedOptions) => {
    if (!isPremium) {
      // 무료 사용자는 프리미엄 옵션을 선택할 수 없음
      return
    }
    setSelectedOptions(prev => ({
      ...prev,
      [option]: !prev[option],
    }))
  }

  const handleStartConversion = async () => {
    if (!selectedFile) return

    // 프리미엄 기능 사용 시 로그인 필요
    const isUsingPremiumFeatures =
      selectedOptions.ocr || selectedOptions.llm || selectedOptions.highQualityImages
    if (isUsingPremiumFeatures && !user) {
      navigate('/login', {
        state: {
          from: '/upload',
          message: '프리미엄 기능을 사용하려면 로그인이 필요합니다.',
          intendedFile: selectedFile,
          intendedOptions: selectedOptions,
        },
      })
      return
    }

    setIsProcessing(true)

    try {
      // TODO: 파일 변환 로직 구현
      // 1. 파일 업로드
      // 2. 변환 작업 큐에 추가
      // 3. 진행 상황 페이지로 이동

      // 임시로 진행 상황 페이지로 이동
      navigate('/convert', {
        state: {
          file: selectedFile,
          options: selectedOptions,
          userId: user?.id || 'anonymous',
        },
      })
    } catch (error) {
      // TODO: 에러 처리
      // eslint-disable-next-line no-console
      console.error('변환 시작 실패:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
      {/* Enhanced Header */}
      <header className="bg-white/80 dark:bg-slate-800/80 backdrop-blur border-b border-slate-200 dark:border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Title */}
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/')}
                className="flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
              >
                <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                  />
                </svg>
                홈으로
              </button>
              <div className="hidden lg:block">
                <h1 className="text-xl font-semibold text-slate-900 dark:text-white">
                  PDF 파일 업로드
                </h1>
              </div>
            </div>

            {/* User Status */}
            <div className="flex items-center space-x-4">
              {!user ? (
                <Button
                  variant="premium"
                  size="sm"
                  onClick={() => navigate('/login', { state: { from: '/upload' } })}
                >
                  로그인
                </Button>
              ) : (
                <div className="flex items-center space-x-3">
                  {isPremium && (
                    <div className="badge badge-premium flex items-center space-x-1">
                      <Crown className="w-3 h-3" />
                      <span>프리미엄</span>
                    </div>
                  )}

                  <div className="text-sm text-slate-600 dark:text-slate-400 hidden sm:block">
                    {user.email}
                  </div>

                  <Button variant="ghost" size="sm">
                    로그아웃
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 lg:px-12 py-8">
        {/* Enhanced File Size Notice */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-xl p-4 mb-8">
          <div className="flex items-center">
            <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400 mr-3" />
            <p className="text-sm text-blue-800 dark:text-blue-300">
              {isPremium ? `최대 300MB PDF 파일 지원` : `최대 10MB PDF 파일 (프리미엄: 300MB)`}
            </p>
          </div>
        </div>

        {/* Enhanced Guest Notice */}
        {!user && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-xl p-6 mb-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Crown className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-3" />
                <div>
                  <h4 className="font-medium text-yellow-800 dark:text-yellow-300">게스트 모드</h4>
                  <p className="text-sm text-yellow-700 dark:text-yellow-400">
                    로그인하지 않은 상태로 기본 변환 기능을 사용할 수 있습니다.
                  </p>
                </div>
              </div>
              <Button
                variant="premium"
                size="sm"
                onClick={() => navigate('/login', { state: { from: '/upload' } })}
              >
                로그인
              </Button>
            </div>
          </div>
        )}

        {/* Enhanced 2-Column Layout */}
        <div className="grid lg:grid-cols-12 gap-8">
          {/* Main Upload Area */}
          <div className="lg:col-span-8">
            {/* Enhanced Upload Zone */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-8 lg:p-12 mb-6 min-h-[450px] flex flex-col justify-center">
              <div className="text-center mb-8">
                <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
                  PDF 파일 업로드
                </h2>
                <p className="text-lg text-slate-600 dark:text-slate-400">
                  변환할 PDF 파일을 드래그 앤 드롭하거나 클릭하여 선택하세요
                </p>
              </div>

              <FileUploadComponent
                onFileSelect={handleFileSelect}
                maxSize={maxFileSize}
                accept=".pdf"
              />
            </div>

            {/* Enhanced File Info */}
            {selectedFile && (
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <FileText className="w-10 h-10 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900 dark:text-white">
                        {selectedFile.name}
                      </h3>
                      <p className="text-sm text-slate-500 dark:text-gray-400">
                        {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • {selectedFile.type}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedFile(null)}
                    className="text-slate-400 hover:text-slate-600 dark:hover:text-gray-300 p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Options Sidebar */}
          <div className="lg:col-span-4">
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6 mb-6">
              <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-6">
                변환 옵션
              </h3>

              <div className="space-y-4">
                {/* Basic Option (Free) */}
                <div className="flex items-center p-4 bg-slate-50 dark:bg-slate-700 rounded-xl">
                  <input type="checkbox" defaultChecked disabled className="w-5 h-5 mr-4" />
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <FileText className="w-4 h-4 mr-3 text-slate-600 dark:text-gray-400" />
                      <span className="font-medium text-slate-900 dark:text-white">
                        기본 텍스트 추출
                      </span>
                    </div>
                    <p className="text-sm text-slate-500 dark:text-gray-400">
                      PDF의 텍스트 내용 추출
                    </p>
                  </div>
                </div>

                {/* OCR Option */}
                <div
                  className={`flex items-center p-4 rounded-xl transition-all ${!isPremium ? 'bg-slate-100 dark:bg-slate-700 opacity-60' : 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-gray-600 hover:shadow-md'}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedOptions.ocr}
                    onChange={() => handleOptionChange('ocr')}
                    disabled={!isPremium}
                    className="w-5 h-5 mr-4"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center">
                        <FileText className="w-4 h-4 mr-3 text-slate-600 dark:text-gray-400" />
                        <span className="font-medium text-slate-900 dark:text-white">
                          OCR 텍스트 인식
                        </span>
                      </div>
                      {!isPremium && <Crown className="w-4 h-4 text-yellow-500" />}
                    </div>
                    <p className="text-sm text-slate-500 dark:text-gray-400">
                      스캔된 문서의 텍스트 추출
                    </p>
                  </div>
                </div>

                {/* LLM Option */}
                <div
                  className={`flex items-center p-4 rounded-xl transition-all ${!isPremium ? 'bg-slate-100 dark:bg-slate-700 opacity-60' : 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-gray-600 hover:shadow-md'}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedOptions.llm}
                    onChange={() => handleOptionChange('llm')}
                    disabled={!isPremium}
                    className="w-5 h-5 mr-4"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center">
                        <Brain className="w-4 h-4 mr-3 text-slate-600 dark:text-gray-400" />
                        <span className="font-medium text-slate-900 dark:text-white">
                          AI 문맥 개선
                        </span>
                      </div>
                      {!isPremium && <Crown className="w-4 h-4 text-yellow-500" />}
                    </div>
                    <p className="text-sm text-slate-500 dark:text-gray-400">
                      DeepSeek AI로 문맥 연결
                    </p>
                  </div>
                </div>

                {/* High Quality Images */}
                <div
                  className={`flex items-center p-4 rounded-xl transition-all ${!isPremium ? 'bg-slate-100 dark:bg-slate-700 opacity-60' : 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-gray-600 hover:shadow-md'}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedOptions.highQualityImages}
                    onChange={() => handleOptionChange('highQualityImages')}
                    disabled={!isPremium}
                    className="w-5 h-5 mr-4"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center">
                        <Image className="w-4 h-4 mr-3 text-slate-600 dark:text-gray-400" />
                        <span className="font-medium text-slate-900 dark:text-white">
                          고해상도 이미지
                        </span>
                      </div>
                      {!isPremium && <Crown className="w-4 h-4 text-yellow-500" />}
                    </div>
                    <p className="text-sm text-slate-500 dark:text-gray-400">
                      최대 품질 이미지 유지
                    </p>
                  </div>
                </div>
              </div>

              {/* Quick Info */}
              <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                <div className="flex items-center mb-2">
                  <Zap className="w-4 h-4 text-blue-600 dark:text-blue-400 mr-2" />
                  <span className="text-sm font-medium text-slate-900 dark:text-white">
                    빠른 변환
                  </span>
                </div>
                <p className="text-xs text-slate-600 dark:text-gray-400">
                  평균 변환 시간: 30초 - 2분 (파일 크기에 따라 다름)
                </p>
              </div>
            </div>

            {/* Premium Upgrade Notice */}
            {!isPremium && (
              <div className="bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 border border-yellow-200 dark:border-yellow-700 rounded-xl p-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center">
                    <Crown className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2" />
                    <h4 className="font-medium text-yellow-800 dark:text-yellow-300">
                      프리미엄 기능 잠금 해제
                    </h4>
                  </div>
                </div>
                <p className="text-sm text-yellow-700 dark:text-yellow-400 mb-4">
                  AI 기술로 더 나은 변환 결과를 얻으세요
                </p>

                <div className="space-y-3 mb-6">
                  <div className="flex items-center text-sm">
                    <Shield className="w-4 h-4 text-yellow-600 dark:text-yellow-400 mr-2" />
                    <span>고급 OCR 기능</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <Brain className="w-4 h-4 text-yellow-600 dark:text-yellow-400 mr-2" />
                    <span>AI 문맥 개선</span>
                  </div>
                </div>

                <Button
                  variant="premium"
                  size="lg"
                  onClick={() => navigate('/premium')}
                  className="w-full"
                >
                  업그레이드하기
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Enhanced Convert Button */}
        {selectedFile && (
          <div className="mt-12 text-center">
            <Button
              onClick={handleStartConversion}
              disabled={isProcessing}
              isLoading={isProcessing}
              size="xl"
              className="px-16 py-5 text-xl shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all"
            >
              {isProcessing ? (
                <>
                  <div className="loading-spinner w-5 h-5 mr-3"></div>
                  변환 준비 중...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5 mr-3" />
                  변환 시작
                </>
              )}
            </Button>

            {!isProcessing && (
              <p className="mt-4 text-sm text-slate-600 dark:text-gray-400">
                선택된 옵션에 따라 변환 시간이 달라질 수 있습니다
              </p>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default FileUpload
