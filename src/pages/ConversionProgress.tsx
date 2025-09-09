import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ProgressTracker } from '../components/common'
import { FileText, Brain, Download, Clock, AlertCircle } from 'lucide-react'

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
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <button onClick={handleCancel} className="text-red-600 hover:text-red-700 font-medium">
              취소
            </button>
            <h1 className="text-2xl font-bold text-gray-900">변환 진행 중</h1>
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
        {/* 파일 정보 */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">변환 파일 정보</h2>
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">파일명</p>
              <p className="font-medium">{file.name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">파일 크기</p>
              <p className="font-medium">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">예상 소요 시간</p>
              <p className="font-medium flex items-center">
                <Clock className="w-4 h-4 mr-1" />
                {Math.ceil(estimatedTime / 1000)}초
              </p>
            </div>
          </div>
        </div>

        {/* 진행 상황 */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">변환 진행 상황</h2>
          <ProgressTracker steps={steps} currentStep={steps[currentStep]?.id} />
        </div>

        {/* 광고 (무료 사용자만) */}
        {!isPremium && (
          <div className="bg-gray-100 rounded-lg p-6 mb-8 text-center">
            <p className="text-gray-600 mb-4">광고</p>
            <div className="bg-white rounded p-8 border-2 border-dashed border-gray-300">
              <p className="text-gray-500">Google AdSense 광고가 표시됩니다</p>
            </div>
            <p className="text-sm text-gray-500 mt-4">
              광고를 제거하고 더 나은 경험을 원하신다면 프리미엄으로 업그레이드하세요.
            </p>
          </div>
        )}

        {/* 옵션 정보 */}
        {(options.ocr || options.llm || options.highQualityImages) && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
            <h3 className="text-lg font-semibold text-blue-900 mb-3">적용된 프리미엄 옵션</h3>
            <div className="space-y-2">
              {options.ocr && (
                <div className="flex items-center text-blue-800">
                  <FileText className="w-4 h-4 mr-2" />
                  <span>OCR 텍스트 인식 활성화</span>
                </div>
              )}
              {options.llm && (
                <div className="flex items-center text-blue-800">
                  <Brain className="w-4 h-4 mr-2" />
                  <span>AI 문맥 개선 활성화</span>
                </div>
              )}
              {options.highQualityImages && (
                <div className="flex items-center text-blue-800">
                  <Download className="w-4 h-4 mr-2" />
                  <span>고해상도 이미지 처리 활성화</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 에러 메시지 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-8">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
              <div>
                <h3 className="text-lg font-semibold text-red-800">변환 실패</h3>
                <p className="text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* 완료 메시지 */}
        {!isProcessing && !error && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
            <h3 className="text-lg font-semibold text-green-800 mb-2">변환 완료!</h3>
            <p className="text-green-700">
              변환이 성공적으로 완료되었습니다. 잠시 후 다운로드 페이지로 이동합니다...
            </p>
          </div>
        )}
      </main>
    </div>
  )
}

export default ConversionProgress
