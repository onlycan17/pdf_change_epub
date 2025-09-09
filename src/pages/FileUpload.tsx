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
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 뒤로가기 버튼 */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/')}
            className="flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
          >
            ← 홈으로
          </button>
        </div>

        {/* 파일 크기 제한 안내 */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4 mb-8">
          <div className="flex items-center">
            <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400 mr-2" />
            <p className="text-blue-800 dark:text-blue-300">
              {isPremium
                ? `최대 300MB PDF 파일을 업로드할 수 있습니다.`
                : `최대 10MB PDF 파일을 업로드할 수 있습니다. 프리미엄으로 업그레이드하여 300MB까지 업로드하세요.`}
            </p>
          </div>
        </div>

        {/* 사용자 상태 표시 */}
        {!user && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4 mb-6">
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

        <div className="grid lg:grid-cols-3 gap-8">
          {/* 메인 업로드 영역 */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                PDF 파일 선택
              </h2>
              <FileUploadComponent
                onFileSelect={handleFileSelect}
                maxSize={maxFileSize}
                accept=".pdf"
              />
            </div>

            {/* 선택된 파일 정보 */}
            {selectedFile && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                  파일 정보
                </h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">파일명:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {selectedFile.name}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">파일 크기:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">파일 형식:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {selectedFile.type}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 옵션 설정 */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">변환 옵션</h3>

              {/* 기본 옵션 (무료) */}
              <div className="mb-4">
                <label className="flex items-center cursor-pointer">
                  <input type="checkbox" defaultChecked disabled className="mr-3" />
                  <div className="flex items-center">
                    <FileText className="w-4 h-4 mr-2 text-gray-600 dark:text-gray-400" />
                    <div>
                      <span className="font-medium text-gray-900 dark:text-white">
                        기본 텍스트 추출
                      </span>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        PDF의 텍스트 내용 추출
                      </p>
                    </div>
                  </div>
                </label>
              </div>

              {/* OCR 옵션 */}
              <div className="mb-4">
                <label
                  className={`flex items-center ${!isPremium ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedOptions.ocr}
                    onChange={() => handleOptionChange('ocr')}
                    disabled={!isPremium}
                    className="mr-3"
                  />
                  <div className="flex items-center">
                    <FileText className="w-4 h-4 mr-2 text-gray-600 dark:text-gray-400" />
                    <div>
                      <span className="font-medium text-gray-900 dark:text-white">
                        OCR 텍스트 인식
                      </span>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        스캔된 문서의 텍스트 추출
                      </p>
                    </div>
                  </div>
                </label>
                {!isPremium && <p className="text-xs text-yellow-600 mt-1 ml-7">프리미엄 기능</p>}
              </div>

              {/* LLM 옵션 */}
              <div className="mb-4">
                <label
                  className={`flex items-center ${!isPremium ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedOptions.llm}
                    onChange={() => handleOptionChange('llm')}
                    disabled={!isPremium}
                    className="mr-3"
                  />
                  <div className="flex items-center">
                    <Brain className="w-4 h-4 mr-2 text-gray-600 dark:text-gray-400" />
                    <div>
                      <span className="font-medium text-gray-900 dark:text-white">
                        AI 문맥 개선
                      </span>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        DeepSeek AI로 문맥 연결
                      </p>
                    </div>
                  </div>
                </label>
                {!isPremium && <p className="text-xs text-yellow-600 mt-1 ml-7">프리미엄 기능</p>}
              </div>

              {/* 고해상도 이미지 */}
              <div className="mb-4">
                <label
                  className={`flex items-center ${!isPremium ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedOptions.highQualityImages}
                    onChange={() => handleOptionChange('highQualityImages')}
                    disabled={!isPremium}
                    className="mr-3"
                  />
                  <div className="flex items-center">
                    <Image className="w-4 h-4 mr-2 text-gray-600 dark:text-gray-400" />
                    <div>
                      <span className="font-medium text-gray-900 dark:text-white">
                        고해상도 이미지
                      </span>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        최대 품질 이미지 유지
                      </p>
                    </div>
                  </div>
                </label>
                {!isPremium && <p className="text-xs text-yellow-600 mt-1 ml-7">프리미엄 기능</p>}
              </div>
            </div>

            {/* 프리미엄 업그레이드 안내 */}
            {!isPremium && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
                <div className="flex items-center mb-2">
                  <Crown className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2" />
                  <h4 className="font-medium text-yellow-800 dark:text-yellow-300">
                    프리미엄 기능
                  </h4>
                </div>
                <p className="text-sm text-yellow-700 dark:text-yellow-400 mb-3">
                  프리미엄 플랜으로 업그레이드하여 고급 기능을 이용하세요.
                </p>
                <Button
                  variant="premium"
                  size="sm"
                  onClick={() => navigate('/premium')}
                  className="w-full"
                >
                  프리미엄으로 업그레이드
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* 변환 시작 버튼 */}
        {selectedFile && (
          <div className="text-center">
            <Button
              onClick={handleStartConversion}
              disabled={isProcessing}
              isLoading={isProcessing}
              size="lg"
              className="px-8"
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
