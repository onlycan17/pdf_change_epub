import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { FileUpload as FileUploadComponent, Button } from '../components/common'
import { Crown, FileText, Image, Brain } from 'lucide-react'

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
      // console.error('변환 시작 실패:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 데스크탑 헤더 - 더 넓은 레이아웃으로 정보 밀도 향상 */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/')}
                className="flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
              >
                ← 홈으로
              </button>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">PDF 변환</h1>
            </div>

            {/* 데스크탑용 사용자 상태 표시 - 헤더로 이동 */}
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
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">{user.email}</span>
                  {isPremium && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200">
                      <Crown className="w-3 h-3 mr-1" />
                      프리미엄
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 파일 크기 제한 안내 - 더 컴팩트하게 */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3 mb-6">
          <div className="flex items-center">
            <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400 mr-2 flex-shrink-0" />
            <p className="text-sm text-blue-800 dark:text-blue-300">
              {isPremium ? `최대 300MB PDF 파일` : `최대 10MB PDF 파일 (프리미엄: 300MB)`}
            </p>
          </div>
        </div>

        {/* 게스트 모드 안내 - 모바일에서만 표시 */}
        {!user && (
          <div className="lg:hidden bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Crown className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2" />
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

        {/* 데스크탑 2단 레이아웃 - 더 넓은 공간 활용 */}
        <div className="grid lg:grid-cols-12 gap-8">
          {/* 메인 업로드 영역 - 더 넓은 공간 */}
          <div className="lg:col-span-8">
            {/* 업로드 영역 - 더 큰 드롭존 */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 mb-6 min-h-[400px] flex flex-col justify-center">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                  PDF 파일 업로드
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  변환할 PDF 파일을 드래그 앤 드롭하거나 클릭하여 선택하세요
                </p>
              </div>
              <FileUploadComponent
                onFileSelect={handleFileSelect}
                maxSize={maxFileSize}
                accept=".pdf"
              />
            </div>

            {/* 선택된 파일 정보 - 더 컴팩트하게 */}
            {selectedFile && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <FileText className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        {selectedFile.name}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • {selectedFile.type}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedFile(null)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
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

          {/* 옵션 설정 - 더 컴팩트한 사이드바 */}
          <div className="lg:col-span-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">변환 옵션</h3>

              {/* 옵션들을 더 컴팩트하게 배치 */}
              <div className="space-y-3">
                {/* 기본 옵션 (무료) */}
                <div className="flex items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <input type="checkbox" defaultChecked disabled className="mr-3" />
                  <div className="flex-1">
                    <div className="flex items-center">
                      <FileText className="w-4 h-4 mr-2 text-gray-600 dark:text-gray-400" />
                      <span className="font-medium text-gray-900 dark:text-white text-sm">
                        기본 텍스트 추출
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      PDF의 텍스트 내용 추출
                    </p>
                  </div>
                </div>

                {/* OCR 옵션 */}
                <div
                  className={`flex items-center p-3 rounded-lg ${!isPremium ? 'bg-gray-100 dark:bg-gray-700 opacity-50' : 'bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600'}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedOptions.ocr}
                    onChange={() => handleOptionChange('ocr')}
                    disabled={!isPremium}
                    className="mr-3"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <FileText className="w-4 h-4 mr-2 text-gray-600 dark:text-gray-400" />
                        <span className="font-medium text-gray-900 dark:text-white text-sm">
                          OCR 텍스트 인식
                        </span>
                      </div>
                      {!isPremium && <Crown className="w-4 h-4 text-yellow-500" />}
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      스캔된 문서의 텍스트 추출
                    </p>
                  </div>
                </div>

                {/* LLM 옵션 */}
                <div
                  className={`flex items-center p-3 rounded-lg ${!isPremium ? 'bg-gray-100 dark:bg-gray-700 opacity-50' : 'bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600'}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedOptions.llm}
                    onChange={() => handleOptionChange('llm')}
                    disabled={!isPremium}
                    className="mr-3"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <Brain className="w-4 h-4 mr-2 text-gray-600 dark:text-gray-400" />
                        <span className="font-medium text-gray-900 dark:text-white text-sm">
                          AI 문맥 개선
                        </span>
                      </div>
                      {!isPremium && <Crown className="w-4 h-4 text-yellow-500" />}
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      DeepSeek AI로 문맥 연결
                    </p>
                  </div>
                </div>

                {/* 고해상도 이미지 */}
                <div
                  className={`flex items-center p-3 rounded-lg ${!isPremium ? 'bg-gray-100 dark:bg-gray-700 opacity-50' : 'bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600'}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedOptions.highQualityImages}
                    onChange={() => handleOptionChange('highQualityImages')}
                    disabled={!isPremium}
                    className="mr-3"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <Image className="w-4 h-4 mr-2 text-gray-600 dark:text-gray-400" />
                        <span className="font-medium text-gray-900 dark:text-white text-sm">
                          고해상도 이미지
                        </span>
                      </div>
                      {!isPremium && <Crown className="w-4 h-4 text-yellow-500" />}
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      최대 품질 이미지 유지
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* 프리미엄 업그레이드 안내 - 더 미니멀하게 */}
            {!isPremium && (
              <div className="bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center">
                    <Crown className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2" />
                    <h4 className="font-medium text-yellow-800 dark:text-yellow-300">
                      프리미엄 기능 잠금 해제
                    </h4>
                  </div>
                </div>
                <p className="text-sm text-yellow-700 dark:text-yellow-400 mb-3">
                  AI 기술로 더 나은 변환 결과를 얻으세요
                </p>
                <Button
                  variant="premium"
                  size="sm"
                  onClick={() => navigate('/premium')}
                  className="w-full"
                >
                  업그레이드하기
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* 변환 시작 버튼 - 더 눈에 띄게 */}
        {selectedFile && (
          <div className="mt-8 text-center">
            <Button
              onClick={handleStartConversion}
              disabled={isProcessing}
              isLoading={isProcessing}
              size="lg"
              className="px-12 py-4 text-lg"
            >
              {isProcessing ? '변환 준비 중...' : '변환 시작'}
            </Button>
          </div>
        )}
      </main>
    </div>
  )
}

export default FileUpload
