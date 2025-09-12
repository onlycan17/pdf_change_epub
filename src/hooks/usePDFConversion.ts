import { useState, useCallback } from 'react'
import {
  ConversionOrchestrator,
  ConversionOptions,
  ConversionProgress,
  ConversionResult,
} from '../services'

export interface UsePDFConversionReturn {
  convertPDF: (file: File, options?: ConversionOptions) => Promise<void>
  isConverting: boolean
  progress: number
  result: ConversionResult | null
  error: string | null
  stages: ConversionProgress[]
  reset: () => void
}

export const usePDFConversion = (): UsePDFConversionReturn => {
  const [isConverting, setIsConverting] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<ConversionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [stages, setStages] = useState<ConversionProgress[]>([])

  const handleProgress = useCallback((progress: ConversionProgress) => {
    setProgress(progress.progress)
    setStages(prev => [...prev, progress])
  }, [])

  const convertPDF = useCallback(
    async (file: File, options: ConversionOptions = {}) => {
      try {
        setIsConverting(true)
        setError(null)
        setResult(null)
        setStages([])
        setProgress(0)

        // 진행률 콜백이 있는 새로운 오케스트레이터 인스턴스 생성
        const orchestrator = new ConversionOrchestrator(handleProgress)

        const conversionResult = await orchestrator.convertPDFToMarkdown(file, options)

        if (conversionResult.success) {
          setResult(conversionResult)
        } else {
          setError(conversionResult.error || '변환 실패')
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다'
        setError(errorMessage)
        setStages(prev => [
          ...prev,
          {
            stage: 'complete',
            progress: 100,
            message: `변환 실패: ${errorMessage}`,
          },
        ])
      } finally {
        setIsConverting(false)
      }
    },
    [handleProgress]
  )

  const reset = useCallback(() => {
    setIsConverting(false)
    setProgress(0)
    setResult(null)
    setError(null)
    setStages([])
  }, [])

  return {
    convertPDF,
    isConverting,
    progress,
    result,
    error,
    stages,
    reset,
  }
}
