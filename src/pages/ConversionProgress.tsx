import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ProgressTracker } from '../components/common'
import {
  FileText,
  Brain,
  Download,
  Clock,
  AlertCircle,
  Crown,
  CheckCircle2,
  Loader2,
} from 'lucide-react'

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
  const [startTime] = useState(Date.now())
  const [elapsedTime, setElapsedTime] = useState(0)

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

  // 경과 시간 업데이트
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)

    return () => clearInterval(timer)
  }, [startTime])

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

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  if (!file) {
    return null
  }

  const progressPercentage = Math.round(((currentStep + 1) / steps.length) * 100)
  const currentStepData = steps[currentStep]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100 dark:from-slate-900 dark:to-slate-800">
      {/* 헤더 */}
      <header className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md border-b border-gray-200/50 dark:border-slate-700/50 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <button
              onClick={handleCancel}
              className="flex items-center px-4 py-2 text-red-600 hover:text-red-700 font-medium transition-all rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              <div className="w-8 h-8 rounded-full bg-red-50 dark:bg-red-900/20 flex items-center justify-center mr-2">
                <span className="text-red-600 dark:text-red-400">✕</span>
              </div>
              취소
            </button>
            <div className="flex items-center space-x-3">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">PDF 변환 중</h1>
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

      {/* 메인 콘텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid lg:grid-cols-12 gap-6">
          {/* 사이드바 */}
          <div className="lg:col-span-3">
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6 mb-6 sticky top-24">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <Clock className="w-5 h-5 mr-2 text-blue-500" />
                진행 상황
              </h3>

              <div className="space-y-3">
                {steps.map((step, index) => (
                  <div
                    key={step.id}
                    className={`flex items-center p-3 rounded-lg transition-all duration-300 ${
                      step.status === 'completed'
                        ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                        : step.status === 'processing'
                          ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 shadow-sm'
                          : 'bg-gray-50 dark:bg-slate-700/50 border border-transparent hover:border-gray-200 dark:hover:border-slate-600'
                    }`}
                  >
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 text-sm font-bold transition-all ${
                        step.status === 'completed'
                          ? 'bg-green-500 text-white shadow-md'
                          : step.status === 'processing'
                            ? 'bg-blue-500 text-white animate-pulse shadow-md'
                            : 'bg-gray-200 dark:bg-slate-600 text-gray-500 dark:text-slate-400'
                      }`}
                    >
                      {step.status === 'completed' ? (
                        <CheckCircle2 className="w-4 h-4" />
                      ) : step.status === 'processing' ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        index + 1
                      )}
                    </div>
                    <div className="flex-1">
                      <div
                        className={`font-medium ${step.status === 'processing' ? 'text-blue-600 dark:text-blue-400' : step.status === 'completed' ? 'text-green-600 dark:text-green-400' : 'text-gray-700 dark:text-slate-300'}`}
                      >
                        {step.label}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-slate-400 mt-1">
                        {step.description}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 pt-4 border-t border-gray-200 dark:border-slate-700">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500 dark:text-slate-400">경과 시간</span>
                  <span className="font-medium text-gray-700 dark:text-slate-300">
                    {formatTime(elapsedTime)}
                  </span>
                </div>
              </div>
            </div>

            {/* 파일 정보 */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <FileText className="w-5 h-5 mr-2 text-blue-500" />
                파일 정보
              </h3>

              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-slate-700">
                  <span className="text-sm text-gray-500 dark:text-slate-400">파일명</span>
                  <span className="text-sm font-medium text-gray-700 dark:text-slate-300 truncate max-w-[120px]">
                    {file.name}
                  </span>
                </div>

                <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-slate-700">
                  <span className="text-sm text-gray-500 dark:text-slate-400">크기</span>
                  <span className="text-sm font-medium text-gray-700 dark:text-slate-300">
                    {(file.size / (1024 * 1024)).toFixed(1)} MB
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500 dark:text-slate-400">진행률</span>
                  <span className="text-sm font-medium text-gray-700 dark:text-slate-300">
                    {progressPercentage}%
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100 dark:border-slate-700">
                <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${progressPercentage}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* 메인 콘텐츠 영역 */}
          <div className="lg:col-span-9">
            {/* 진행 상황 메인 패널 */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-8 mb-6">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">변환 진행 상황</h2>
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                  <span className="text-sm text-gray-600 dark:text-slate-400">처리 중</span>
                </div>
              </div>

              {/* 현재 단계 강조 */}
              <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
                <div className="flex items-center space-x-4 mb-2">
                  <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center">
                    {currentStepData.status === 'processing' ? (
                      <Loader2 className="w-6 h-6 text-white animate-spin" />
                    ) : currentStepData.status === 'completed' ? (
                      <CheckCircle2 className="w-6 h-6 text-white" />
                    ) : (
                      <span className="text-white font-bold">{currentStep + 1}</span>
                    )}
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                      {currentStepData.label}
                    </h3>
                    <p className="text-gray-600 dark:text-slate-400">
                      {currentStepData.description}
                    </p>
                  </div>
                </div>
              </div>

              {/* 전체 진행률 */}
              <div className="mb-8">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-lg font-medium text-gray-700 dark:text-slate-300">
                    전체 진행률
                  </span>
                  <span className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                    {progressPercentage}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-4">
                  <div
                    className="bg-gradient-to-r from-blue-500 via-blue-600 to-indigo-600 h-4 rounded-full transition-all duration-700 ease-out shadow-lg"
                    style={{ width: `${progressPercentage}%` }}
                  ></div>
                </div>
              </div>

              {/* 상세 진행 트래커 */}
              <ProgressTracker steps={steps} currentStep={steps[currentStep]?.id} />
            </div>

            {/* 옵션 정보 & 상태 메시지 */}
            <div className="grid md:grid-cols-2 gap-6 mb-6">
              {/* 옵션 정보 */}
              {(options.ocr || options.llm || options.highQualityImages) && (
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6 shadow-lg">
                  <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-300 mb-4 flex items-center">
                    <Crown className="w-5 h-5 mr-2" />
                    프리미엄 옵션
                  </h3>
                  <div className="space-y-3">
                    {options.ocr && (
                      <div className="flex items-center text-blue-800 dark:text-blue-400">
                        <FileText className="w-5 h-5 mr-3" />
                        <span>OCR 텍스트 인식</span>
                      </div>
                    )}
                    {options.llm && (
                      <div className="flex items-center text-blue-800 dark:text-blue-400">
                        <Brain className="w-5 h-5 mr-3" />
                        <span>AI 문맥 개선</span>
                      </div>
                    )}
                    {options.highQualityImages && (
                      <div className="flex items-center text-blue-800 dark:text-blue-400">
                        <Download className="w-5 h-5 mr-3" />
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
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 shadow-lg">
                    <div className="flex items-center">
                      <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400 mr-3" />
                      <div>
                        <h3 className="text-lg font-semibold text-red-800 dark:text-red-300">
                          변환 실패
                        </h3>
                        <p className="text-red-700 dark:text-red-400 mt-1">{error}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* 완료 메시지 */}
                {!isProcessing && !error && (
                  <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-6 shadow-lg">
                    <div className="flex items-center">
                      <CheckCircle2 className="w-6 h-6 text-green-600 dark:text-green-400 mr-3" />
                      <div>
                        <h3 className="text-lg font-semibold text-green-800 dark:text-green-300">
                          변환 완료!
                        </h3>
                        <p className="text-green-700 dark:text-green-400 mt-1">
                          곧 다운로드 페이지로 이동합니다...
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 광고 (무료 사용자만) */}
            {!isPremium && (
              <div className="bg-gradient-to-r from-gray-100 to-slate-200 dark:from-slate-700 dark:to-slate-800 rounded-xl p-6 text-center border border-gray-200 dark:border-slate-700 shadow-lg">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm text-gray-600 dark:text-slate-400">광고</p>
                  <button
                    onClick={() => navigate('/premium')}
                    className="text-sm text-blue-600 dark:text-blue-400 hover:underline font-medium"
                  >
                    광고 제거하기
                  </button>
                </div>
                <div className="bg-white dark:bg-slate-600 rounded-lg p-6 border-2 border-dashed border-gray-300 dark:border-slate-500">
                  <p className="text-gray-500 dark:text-slate-400">Google AdSense 광고</p>
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
