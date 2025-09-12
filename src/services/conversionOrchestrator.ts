import { logger } from '../utils/logger'
import { pdfProcessor, PDFProcessingResult, PDFPage } from './pdfProcessor'
import { ocrProcessor } from './ocrProcessor'
import { markdownConverter } from './markdownConverter'

export interface ConversionOptions {
  useOCR?: boolean
  ocrLanguage?: string
  markdownOptions?: {
    preserveFormatting?: boolean
    includePageNumbers?: boolean
    headingDetection?: boolean
    listDetection?: boolean
    tableDetection?: boolean
  }
}

export interface ConversionProgress {
  stage: 'upload' | 'processing' | 'ocr' | 'conversion' | 'complete'
  progress: number // 0-100
  message: string
  details?: {
    pageCount?: number
    totalImages?: number
    totalTextLength?: number
    wordCount?: number
    headingCount?: number
    listCount?: number
    processingTime?: number
    [key: string]: unknown // 추가 필드를 위한 인덱스 시그니처
  }
}

export interface ConversionResult {
  success: boolean
  markdown?: string
  metadata?: {
    title?: string
    author?: string
    pageCount: number
    wordCount: number
    processingTime: number
  }
  error?: string
  stages: ConversionProgress[]
}

export class ConversionOrchestrator {
  private onProgress?: (progress: ConversionProgress) => void

  constructor(onProgress?: (progress: ConversionProgress) => void) {
    this.onProgress = onProgress
  }

  async convertPDFToMarkdown(
    file: File,
    options: ConversionOptions = {}
  ): Promise<ConversionResult> {
    const startTime = Date.now()
    const stages: ConversionProgress[] = []

    try {
      // 1. 파일 업로드 및 유효성 검사
      this.updateProgress(stages, {
        stage: 'upload',
        progress: 10,
        message: '파일 업로드 및 유효성 검사 중...',
      })

      const validation = pdfProcessor.validatePDFFile(file)
      if (!validation.valid) {
        throw new Error(validation.error || '파일 유효성 검사 실패')
      }

      // 2. PDF 처리
      this.updateProgress(stages, {
        stage: 'processing',
        progress: 25,
        message: 'PDF 문서 분석 중...',
      })

      const pdfResult = await pdfProcessor.processPDF(file)

      this.updateProgress(stages, {
        stage: 'processing',
        progress: 45,
        message: `PDF 처리 완료: ${pdfResult.pages.length}페이지`,
        details: {
          pageCount: pdfResult.pages.length,
          totalImages: pdfResult.totalImages,
          totalTextLength: pdfResult.totalTextLength,
        },
      })

      let finalPages = pdfResult.pages

      // 3. OCR 처리 (필요한 경우)
      if (options.useOCR) {
        this.updateProgress(stages, {
          stage: 'ocr',
          progress: 50,
          message: 'OCR 텍스트 인식 중...',
        })

        finalPages = await this.performOCRWithProgress(pdfResult, options.ocrLanguage, progress => {
          this.updateProgress(stages, {
            stage: 'ocr',
            progress: 50 + Math.floor(progress * 30), // 50-80%
            message: `OCR 처리 중: ${Math.floor(progress * 100)}%`,
          })
        })
      }

      // 4. 마크다운 변환
      this.updateProgress(stages, {
        stage: 'conversion',
        progress: 80,
        message: '마크다운 변환 중...',
      })

      const markdownResult = await markdownConverter.convertToMarkdown(
        finalPages,
        options.markdownOptions
      )

      this.updateProgress(stages, {
        stage: 'conversion',
        progress: 95,
        message: '마크다운 변환 완료',
        details: {
          wordCount: markdownResult.wordCount,
          headingCount: markdownResult.headingCount,
          listCount: markdownResult.listCount,
        },
      })

      // 5. 완료
      const processingTime = Date.now() - startTime

      this.updateProgress(stages, {
        stage: 'complete',
        progress: 100,
        message: '변환 완료',
        details: {
          processingTime,
        },
      })

      return {
        success: true,
        markdown: markdownResult.markdown,
        metadata: {
          title: pdfResult.metadata.title,
          author: pdfResult.metadata.author,
          pageCount: pdfResult.metadata.pageCount,
          wordCount: markdownResult.wordCount,
          processingTime,
        },
        stages,
      }
    } catch (error) {
      logger.error('PDF to Markdown 변환 실패', error)

      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류'

      this.updateProgress(stages, {
        stage: 'complete',
        progress: 100,
        message: `변환 실패: ${errorMessage}`,
      })

      return {
        success: false,
        error: errorMessage,
        stages,
      }
    } finally {
      // 리소스 정리
      await this.cleanup()
    }
  }

  private async performOCRWithProgress(
    pdfResult: PDFProcessingResult,
    _language?: string,
    onProgress?: (progress: number) => void
  ): Promise<PDFPage[]> {
    try {
      logger.info('OCR 처리 시작', { pageCount: pdfResult.pages.length })

      const totalPages = pdfResult.pages.length
      const results: PDFPage[] = []

      // 페이지별로 순차적으로 처리하여 진행률 추적
      for (let i = 0; i < totalPages; i++) {
        const page = pdfResult.pages[i]

        try {
          // 페이지를 이미지로 변환 (간단한 텍스트 기반 OCR 시뮬레이션)
          // 실제 구현에서는 PDF.js를 사용하여 페이지를 캔버스로 렌더링해야 함
          const ocrResult = await ocrProcessor.processPDFPage(
            this.simulatePageImage(page.text),
            i + 1
          )

          results.push({
            ...page,
            text: ocrResult.text || page.text, // OCR 결과가 없으면 원본 텍스트 사용
          })
        } catch (error) {
          logger.warn(`페이지 ${i + 1} OCR 실패, 원본 텍스트 사용`, error)
          results.push(page)
        }

        // 진행률 업데이트
        if (onProgress) {
          onProgress((i + 1) / totalPages)
        }
      }

      logger.info('OCR 처리 완료', {
        totalPages: results.length,
        successfulOCR: results.filter((p, i) => p.text !== pdfResult.pages[i]?.text).length,
      })

      return results
    } catch (error) {
      logger.error('OCR 처리 중 오류', error)
      // OCR 실패시 원본 페이지 반환
      return pdfResult.pages
    }
  }

  // 실제 구현에서는 PDF 페이지를 이미지로 변환해야 함
  private simulatePageImage(text: string): string {
    // 현재는 텍스트를 기반으로 간단한 OCR 시뮬레이션
    // 실제 구현에서는 PDF.js를 사용하여 페이지를 캔버스로 렌더링하고
    // 그 캔버스를 이미지 데이터로 변환해야 함
    return `data:text/plain;base64,${btoa(text)}`
  }

  private updateProgress(stages: ConversionProgress[], progress: ConversionProgress): void {
    stages.push(progress)
    if (this.onProgress) {
      this.onProgress(progress)
    }
    logger.info('변환 진행률 업데이트', progress)
  }

  private async cleanup(): Promise<void> {
    try {
      // OCR 프로세서 정리
      await ocrProcessor.cleanup()
      logger.info('리소스 정리 완료')
    } catch (error) {
      logger.warn('리소스 정리 중 오류', error)
    }
  }

  // 변환 상태 확인
  getConversionStatus(stages: ConversionProgress[]): string {
    if (stages.length === 0) {
      return '대기 중'
    }

    const lastStage = stages[stages.length - 1]
    return lastStage.message
  }

  // 변환 진행률 계산
  getOverallProgress(stages: ConversionProgress[]): number {
    if (stages.length === 0) {
      return 0
    }

    const lastStage = stages[stages.length - 1]
    return lastStage.progress
  }
}

// 싱글톤 인스턴스
export const conversionOrchestrator = new ConversionOrchestrator()
