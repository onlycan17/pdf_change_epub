import { supabase } from './supabase'
import { logger } from '../utils/logger'
import type { ConversionResult } from '../types/conversion'
import { mapConversionRowToResult } from '../utils/mappers'

export interface ConversionOptions {
  format: 'epub' | 'mobi' | 'azw3'
  quality?: 'high' | 'medium' | 'low'
  preserveImages?: boolean
  extractText?: boolean
  pageRange?: {
    start: number
    end: number
  }
}

export interface ConversionProgress {
  status: 'queued' | 'processing' | 'completed' | 'failed'
  percentage: number
  message: string
  currentStep?: string
  estimatedTime?: number
}

// ConversionResult는 src/types/conversion 에서 관리

export class ConversionService {
  private static instance: ConversionService
  private conversionJobs: Map<string, number> = new Map()

  private constructor() {}

  static getInstance(): ConversionService {
    if (!ConversionService.instance) {
      ConversionService.instance = new ConversionService()
    }
    return ConversionService.instance
  }

  async convertFile(
    fileId: string,
    fileName: string,
    options: ConversionOptions,
    onProgress?: (progress: ConversionProgress) => void
  ): Promise<ConversionResult> {
    try {
      // 변환 작업 시작
      const conversionId = `conv_${Date.now()}`

      // 초기 진행률 설정
      if (onProgress) {
        onProgress({
          status: 'queued',
          percentage: 0,
          message: '변환 대기 중...',
          currentStep: '대기',
        })
      }

      // 실제 변환 로직 (시뮬레이션)
      await this.simulateConversion(conversionId, options, onProgress)

      // 변환된 파일 URL 생성 (실제로는 서버에서 처리)
      const convertedFileName = fileName.replace(/\.pdf$/i, `.${options.format}`)
      const convertedFileUrl = `${window.location.origin}/api/converted/${conversionId}/${convertedFileName}`

      // 변환 결과 저장
      const result: ConversionResult = {
        id: conversionId,
        originalFileId: fileId,
        originalFileName: fileName,
        convertedFileUrl,
        convertedFileName,
        format: options.format,
        size: Math.floor(Math.random() * 5000000) + 1000000, // 시뮬레이션용 크기
        createdAt: new Date(),
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24시간 후 만료
      }

      // 데이터베이스에 변환 기록 저장
      await this.saveConversionRecord(result)

      return result
    } catch (error) {
      logger.error('파일 변환 중 오류 발생:', error)
      throw new Error(
        `파일 변환 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
      )
    }
  }

  private async simulateConversion(
    _conversionId: string,
    _options: ConversionOptions,
    onProgress?: (progress: ConversionProgress) => void
  ): Promise<void> {
    const steps = [
      { name: '파일 분석 중...', duration: 1000 },
      { name: '텍스트 추출 중...', duration: 1500 },
      { name: '이미지 처리 중...', duration: 2000 },
      { name: 'EPUB 생성 중...', duration: 2500 },
      { name: '품질 검증 중...', duration: 1000 },
    ]

    let totalProgress = 0
    const stepProgress = 100 / steps.length

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i]

      if (onProgress) {
        onProgress({
          status: 'processing',
          percentage: Math.round(totalProgress),
          message: step.name,
          currentStep: step.name,
          estimatedTime: Math.round((steps.length - i) * 1.5),
        })
      }

      await new Promise(resolve => setTimeout(resolve, step.duration))
      totalProgress += stepProgress
    }

    if (onProgress) {
      onProgress({
        status: 'completed',
        percentage: 100,
        message: '변환 완료!',
        currentStep: '완료',
      })
    }
  }

  private async saveConversionRecord(result: ConversionResult): Promise<void> {
    try {
      const { error } = await supabase.from('conversions').insert({
        id: result.id,
        original_file_id: result.originalFileId,
        original_file_name: result.originalFileName,
        converted_file_url: result.convertedFileUrl,
        converted_file_name: result.convertedFileName,
        format: result.format,
        size: result.size,
        created_at: result.createdAt.toISOString(),
        expires_at: result.expiresAt.toISOString(),
        user_id: (await supabase.auth.getUser()).data.user?.id,
      })

      if (error) {
        logger.error('변환 기록 저장 실패:', error)
      }
    } catch (error) {
      logger.error('변환 기록 저장 중 오류:', error)
    }
  }

  async getConversionStatus(conversionId: string): Promise<ConversionProgress | null> {
    try {
      const { data, error } = await supabase
        .from('conversions')
        .select('status, progress, error_message')
        .eq('id', conversionId)
        .single()

      if (error || !data) {
        return null
      }

      return {
        status: data.status || 'processing',
        percentage: data.progress || 0,
        message: data.error_message || '변환 중...',
      }
    } catch (error) {
      logger.error('변환 상태 조회 중 오류:', error)
      return null
    }
  }

  async getConversionHistory(limit: number = 10): Promise<ConversionResult[]> {
    try {
      const { data, error } = await supabase
        .from('conversions')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(limit)

      if (error) {
        throw error
      }

      return (data || []).map(mapConversionRowToResult)
    } catch (error) {
      logger.error('변환 기록 조회 중 오류:', error)
      return []
    }
  }

  async cancelConversion(conversionId: string): Promise<void> {
    try {
      // 진행 중인 변환 작업 취소
      const job = this.conversionJobs.get(conversionId)
      if (job) {
        clearTimeout(job)
        this.conversionJobs.delete(conversionId)
      }

      // 데이터베이스 상태 업데이트
      const { error } = await supabase
        .from('conversions')
        .update({
          status: 'cancelled',
          updated_at: new Date().toISOString(),
        })
        .eq('id', conversionId)

      if (error) {
        throw error
      }
    } catch (error) {
      logger.error('변환 취소 중 오류:', error)
      throw new Error(
        `변환 취소 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
      )
    }
  }

  async deleteConversion(conversionId: string): Promise<void> {
    try {
      // 변환 기록 삭제
      const { error } = await supabase.from('conversions').delete().eq('id', conversionId)

      if (error) {
        throw error
      }
    } catch (error) {
      logger.error('변환 기록 삭제 중 오류:', error)
      throw new Error(
        `변환 기록 삭제 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
      )
    }
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes'

    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  getFormatDescription(format: string): string {
    const descriptions = {
      epub: '전자책 표준 형식. 대부분의 기기에서 지원됩니다.',
      mobi: 'Amazon Kindle 전용 형식. Kindle 기기에서 최적화됩니다.',
      azw3: 'Amazon의 최신 전자책 형식. 고급 기능을 지원합니다.',
    }

    return descriptions[format as keyof typeof descriptions] || '알 수 없는 형식'
  }
}

export const conversionService = ConversionService.getInstance()
