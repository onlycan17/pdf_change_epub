import { createWorker, Worker, RecognizeResult } from 'tesseract.js'
import { logger } from '../utils/logger'

export interface OCROptions {
  language?: string
  whitelist?: string
  blacklist?: string
  oem?: number
  psm?: number
}

export interface OCRResult {
  text: string
  confidence: number
  blocks: Array<{
    text: string
    confidence: number
    bbox: {
      x: number
      y: number
      width: number
      height: number
    }
  }>
}

export class OCRProcessor {
  private worker: Worker | null = null
  private isInitialized = false

  constructor() {}

  async initialize(): Promise<void> {
    if (this.isInitialized) return

    try {
      logger.info('OCR 워커 초기화 시작')

      this.worker = await createWorker('kor+eng', 1, {
        logger: m => {
          if (m.status === 'recognizing text') {
            logger.debug('OCR 진행률', { progress: m.progress })
          }
        },
      })

      this.isInitialized = true
      logger.info('OCR 워커 초기화 완료')
    } catch (error) {
      logger.error('OCR 워커 초기화 실패', error)
      throw new Error(
        `OCR 초기화 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
      )
    }
  }

  async processImage(
    imageData: string | File | Blob,
    options: OCROptions = {}
  ): Promise<OCRResult> {
    if (!this.isInitialized || !this.worker) {
      await this.initialize()
    }

    try {
      logger.info('OCR 처리 시작', {
        imageType: typeof imageData === 'string' ? 'base64/url' : 'file/blob',
        language: options.language || 'kor+eng',
      })

      const startTime = Date.now()

      // OCR 실행
      const result: RecognizeResult = await this.worker!.recognize(imageData)

      const processingTime = Date.now() - startTime

      // 결과 파싱
      const ocrResult: OCRResult = {
        text: result.data.text?.trim() || '',
        confidence: result.data.confidence || 0,
        blocks: (result.data.blocks || []).map(block => ({
          text: block.text || '',
          confidence: block.confidence || 0,
          bbox: {
            x: block.bbox?.x0 || 0,
            y: block.bbox?.y0 || 0,
            width: (block.bbox?.x1 || 0) - (block.bbox?.x0 || 0),
            height: (block.bbox?.y1 || 0) - (block.bbox?.y0 || 0),
          },
        })),
      }

      logger.info('OCR 처리 완료', {
        processingTime,
        textLength: ocrResult.text.length,
        confidence: ocrResult.confidence,
        blockCount: ocrResult.blocks.length,
      })

      return ocrResult
    } catch (error) {
      logger.error('OCR 처리 중 오류', error)
      throw new Error(
        `OCR 처리 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
      )
    }
  }

  async processPDFPage(pageImage: string, pageNumber: number): Promise<OCRResult> {
    try {
      logger.info(`PDF 페이지 ${pageNumber} OCR 처리 시작`)

      const result = await this.processImage(pageImage, {
        language: 'kor+eng',
        psm: 6, // 단일 균일 텍스트 블록 가정
      })

      logger.info(`PDF 페이지 ${pageNumber} OCR 처리 완료`, {
        textLength: result.text.length,
        confidence: result.confidence,
      })

      return result
    } catch (error) {
      logger.error(`PDF 페이지 ${pageNumber} OCR 처리 실패`, error)
      throw error
    }
  }

  // 이미지 품질 검사
  validateImage(imageData: string | File | Blob): { valid: boolean; error?: string } {
    try {
      if (typeof imageData === 'string') {
        // Base64 문자열 길이 검사 (최소 1KB)
        if (imageData.length < 1024) {
          return {
            valid: false,
            error: '이미지 데이터가 너무 작습니다.',
          }
        }
      } else if (imageData instanceof File) {
        // 파일 크기 검사 (50MB 제한)
        const maxSize = 50 * 1024 * 1024 // 50MB
        if (imageData.size > maxSize) {
          return {
            valid: false,
            error: '이미지 파일이 너무 큽니다. 최대 50MB까지 지원됩니다.',
          }
        }

        // 파일 형식 검사
        const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp']
        if (!validTypes.includes(imageData.type)) {
          return {
            valid: false,
            error: '지원되지 않는 이미지 형식입니다. JPEG, PNG, WebP, BMP만 지원됩니다.',
          }
        }
      }

      return { valid: true }
    } catch (error) {
      logger.error('이미지 유효성 검사 중 오류', error)
      return {
        valid: false,
        error: '이미지 유효성 검사 실패',
      }
    }
  }

  // 워커 종료
  async terminate(): Promise<void> {
    if (this.worker) {
      try {
        await this.worker.terminate()
        this.worker = null
        this.isInitialized = false
        logger.info('OCR 워커 종료 완료')
      } catch (error) {
        logger.error('OCR 워커 종료 중 오류', error)
      }
    }
  }

  // 메모리 정리
  cleanup(): void {
    this.terminate()
  }
}

// 싱글톤 인스턴스
export const ocrProcessor = new OCRProcessor()
