import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ProgressTracker } from '../components/common'
import { FileText, Brain, Download, Clock, AlertCircle, Crown } from 'lucide-react'

interface ConversionStep {
  id: string
  label: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  description?: string
}

const ConversionProgress: React.FC = () => {
  const { user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(0)
  const [isProcessing, setIsProcessing] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [estimatedTime] = useState(0)
  const [startTime] = useState(Date.now())

  const isPremium = user?.is_premium || false
  const file = location.state?.file
  const options = location.state?.options || { ocr: false, llm: false, highQualityImages: false }

  const [steps, setSteps] = useState<ConversionStep[]>([
    {
      id: 'upload',
      label: '파일 업로드',
      status: 'processing',
      description: 'PDF 파일을 서버에 업로드 중...',
    },
    {
      id: 'analyze',
      label: '파일 분석',
      status: 'pending',
      description: 'PDF 구조를 분석하고 페이지 수를 확인 중...',
    },
    {
      id: 'extract',
      label: '텍스트 추출',
      status: 'pending',
      description: 'PDF에서 텍스트를 추출 중...',
    },
  ])

  // OCR 옵션이 있는 경우 OCR 단계 추가
  if (options.ocr) {
    steps.splice(3, 0, {
      id: 'ocr',
      label: 'OCR 텍스트 인식',
      status: 'pending',
      description: '스캔된 문서에서 텍스트를 인식 중...',
    })
  }

  // LLM 옵션이 있는 경우 LLM 단계 추가
  if (options.llm) {
    steps.push({
      id: 'llm',
      label: 'AI 문맥 개선',
      status: 'pending',
      description: 'DeepSeek AI로 문맥을 개선 중...',
    })
  }

  steps.push(
    {
      id: 'convert',
      label: 'EPUB 변환',
      status: 'pending',
      description: 'EPUB 형식으로 변환 중...',
    },
    {
      id: 'complete',
      label: '변환 완료',
      status: 'pending',
      description: '변환이 완료되었습니다!',
    }
  )

  useEffect(() => {
    if (!file) {
      navigate('/upload')
      return
    }

    // 시뮬레이션: 실제 변환 프로세스
    const simulateConversion = async () => {
      try {
        // 1. 파일 업로드 (2초)
        await new Promise(resolve => setTimeout(resolve, 2000))
        updateStepStatus('upload', 'completed')
        updateStepStatus('analyze', 'processing')

        // 2. 파일 분석 (3초)
        await new Promise(resolve => setTimeout(resolve, 3000))
        updateStepStatus('analyze', 'completed')
        updateStepStatus('extract', 'processing')

        // 3. 텍스트 추출 (4초)
        await new Promise(resolve => setTimeout(resolve, 4000))
        updateStepStatus('extract', 'completed')

        // 4. OCR (옵션, 6초)
        if (options.ocr) {
          updateStepStatus('ocr', 'processing')
          await new Promise(resolve => setTimeout(resolve, 6000))
          updateStepStatus('ocr', 'completed')
        }

        // 5. LLM (옵션, 8초)
        if (options.llm) {
          updateStepStatus('llm', 'processing')
          await new Promise(resolve => setTimeout(resolve, 8000))
          updateStepStatus('llm', 'completed')
        }

        // 6. EPUB 변환 (3초)
        updateStepStatus('convert', 'processing')
        await new Promise(resolve => setTimeout(resolve, 3000))
        updateStepStatus('convert', 'completed')
        updateStepStatus('complete', 'completed')

        setIsProcessing(false)

        // 3초 후 다운로드 페이지로 자동 이동
        setTimeout(() => {
          navigate('/download', {
            state: {
              file: file,
              options: options,
              downloadUrl: '#', // 실제 다운로드 URL로 교체
              fileSize: 1024 * 1024, // 1MB 예시
              conversionTime: Date.now() - startTime,
            },
          })
        }, 3000)
      } catch (error) {
        setError('변환 중 오류가 발생했습니다.')
        setIsProcessing(false)
      }
    }

    simulateConversion()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file, options, navigate, startTime])

  const updateStepStatus = (stepId: string, status: ConversionStep['status']) => {
    setSteps(prev => prev.map(step => (step.id === stepId ? { ...step, status } : step)))

    // 현재 단계 업데이트
    const stepIndex = steps.findIndex(step => step.id === stepId)
    if (stepIndex !== -1) {
      setCurrentStep(stepIndex)
    }
  }

  const handleCancel = () => {
    if (window.confirm('정말로 변환을 취소하시겠습니까?')) {
      navigate('/upload')
    }
  }

  if (!file) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 헤더 - 더 컴팩트하게 */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-3">
            <button
              onClick={handleCancel}
              className="flex items-center text-red-600 hover:text-red-700 font-medium transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-red-50 dark:bg-red-900/20 flex items-center justify-center mr-2">
                <span className="text-red-600 dark:text-red-400">✕</span>
              </div>
              취소
            </button>
            <div className="flex items-center space-x-3">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">PDF 변환 중</h1>
              {isPremium && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-yellow-400 to-orange-400 text-white">
                  <Crown className="w-3 h-3 mr-1" />
                  프리미엄
                </span>
              )}
            </div>
            <div className="w-20"></div>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 - 12단 그리드 레이아웃 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid lg:grid-cols-12 gap-6">
          {/* 사이드바 - 현재 단계 정보 */}
          <div className="lg:col-span-3">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 mb-4 sticky top-6">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                현재 진행 상황
              </h3>
              <div className="space-y-2">
                {steps.map((step, index) => (
                  <div
                    key={step.id}
                    className={`flex items-center p-2 rounded-lg text-xs ${
                      step.status === 'completed'
                        ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                        : step.status === 'processing'
                          ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-700'
                          : 'bg-gray-50 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                    }`}
                  >
                    <div
                      className={`w-5 h-5 rounded-full flex items-center justify-center mr-2 text-xs font-bold ${
                        step.status === 'completed'
                          ? 'bg-green-500 text-white'
                          : step.status === 'processing'
                            ? 'bg-blue-500 text-white animate-pulse'
                            : 'bg-gray-300 dark:bg-gray-600 text-gray-600 dark:text-gray-400'
                      }`}
                    >
                      {step.status === 'completed' ? '✓' : index + 1}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">{step.label}</div>
                      <div className="text-xs opacity-75">{step.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 파일 정보 요약 */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                파일 정보
              </h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">파일명:</span>
                  <span className="font-medium text-gray-900 dark:text-white truncate ml-2">
                    {file.name}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">크기:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {(file.size / (1024 * 1024)).toFixed(1)} MB
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">예상 시간:</span>
                  <span className="font-medium text-gray-900 dark:text-white flex items-center">
                    <Clock className="w-3 h-3 mr-1" />
                    {Math.ceil(estimatedTime / 1000)}초
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 메인 콘텐츠 영역 */}
          <div className="lg:col-span-9">
            {/* 진행 상황 메인 패널 */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  변환 진행 상황
                </h2>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">처리 중</span>
                </div>
              </div>

              {/* 진행률 바 */}
              <div className="mb-6">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    전체 진행률
                  </span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {Math.round(((currentStep + 1) / steps.length) * 100)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* 상세 진행 트래커 */}
              <ProgressTracker steps={steps} currentStep={steps[currentStep]?.id} />
            </div>

            {/* 옵션 정보 & 상태 메시지를 한 줄에 */}
            <div className="grid md:grid-cols-2 gap-6 mb-6">
              {/* 옵션 정보 */}
              {(options.ocr || options.llm || options.highQualityImages) && (
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-3">
                    프리미엄 옵션
                  </h3>
                  <div className="space-y-2">
                    {options.ocr && (
                      <div className="flex items-center text-blue-800 dark:text-blue-400 text-sm">
                        <FileText className="w-4 h-4 mr-2" />
                        <span>OCR 텍스트 인식</span>
                      </div>
                    )}
                    {options.llm && (
                      <div className="flex items-center text-blue-800 dark:text-blue-400 text-sm">
                        <Brain className="w-4 h-4 mr-2" />
                        <span>AI 문맥 개선</span>
                      </div>
                    )}
                    {options.highQualityImages && (
                      <div className="flex items-center text-blue-800 dark:text-blue-400 text-sm">
                        <Download className="w-4 h-4 mr-2" />
                        <span>고해상도 이미지</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 상태 메시지 영역 */}
              <div className="space-y-4">
                {/* 에러 메시지 */}
                {error && (
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4">
                    <div className="flex items-center">
                      <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mr-2" />
                      <div>
                        <h3 className="text-sm font-semibold text-red-800 dark:text-red-300">
                          변환 실패
                        </h3>
                        <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* 완료 메시지 */}
                {!isProcessing && !error && (
                  <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-4">
                    <div className="flex items-center">
                      <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center mr-2">
                        <span className="text-white text-xs">✓</span>
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-green-800 dark:text-green-300">
                          변환 완료!
                        </h3>
                        <p className="text-sm text-green-700 dark:text-green-400">
                          곧 다운로드 페이지로 이동합니다...
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 광고 (무료 사용자만) - 더 컴팩트하게 */}
            {!isPremium && (
              <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4 text-center">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-gray-600 dark:text-gray-400">광고</p>
                  <button
                    onClick={() => navigate('/premium')}
                    className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    광고 제거하기
                  </button>
                </div>
                <div className="bg-white dark:bg-gray-600 rounded p-4 border-2 border-dashed border-gray-300 dark:border-gray-500">
                  <p className="text-gray-500 dark:text-gray-400 text-sm">Google AdSense</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default ConversionProgress
