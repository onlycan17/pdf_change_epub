import * as pdfjsLib from 'pdfjs-dist'
import { TextContent } from 'pdfjs-dist/types/src/display/api'
import { logger } from '../utils/logger'

// PDF.js 워커를 로컬 파일로 설정 (보안 강화)
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.js',
  import.meta.url
).toString()

export interface PDFPage {
  pageNumber: number
  text: string
  images: string[]
  width: number
  height: number
}

export interface PDFMetadata {
  title?: string
  author?: string
  subject?: string
  creator?: string
  producer?: string
  creationDate?: Date
  modificationDate?: Date
  pageCount: number
}

export interface PDFProcessingResult {
  metadata: PDFMetadata
  pages: PDFPage[]
  totalImages: number
  totalTextLength: number
}

export class PDFProcessor {
  private workerSrc: string

  constructor() {
    // PDF.js 워커 설정
    this.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`
    pdfjsLib.GlobalWorkerOptions.workerSrc = this.workerSrc
  }

  async processPDF(file: File): Promise<PDFProcessingResult> {
    try {
      logger.info('PDF 처리 시작', { fileName: file.name, fileSize: file.size })

      // 파일을 ArrayBuffer로 변환
      const arrayBuffer = await file.arrayBuffer()
      const pdfData = new Uint8Array(arrayBuffer)

      // PDF 문서 로드
      const pdf = await pdfjsLib.getDocument({
        data: pdfData,
        // 보안 설정
        disableFontFace: false,
        useSystemFonts: true,
      }).promise

      // 메타데이터 추출
      const metadata = await this.extractMetadata(pdf)

      // 페이지별 처리
      const pages: PDFPage[] = []
      let totalImages = 0
      let totalTextLength = 0

      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i)
        const pageData = await this.processPage(page, i)

        pages.push(pageData)
        totalImages += pageData.images.length
        totalTextLength += pageData.text.length
      }

      const result: PDFProcessingResult = {
        metadata,
        pages,
        totalImages,
        totalTextLength,
      }

      logger.info('PDF 처리 완료', {
        pageCount: pdf.numPages,
        totalImages,
        totalTextLength,
      })

      return result
    } catch (error) {
      logger.error('PDF 처리 중 오류 발생', error)
      throw new Error(
        `PDF 처리 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
      )
    }
  }

  private async extractMetadata(pdf: pdfjsLib.PDFDocumentProxy): Promise<PDFMetadata> {
    try {
      const metadata = await pdf.getMetadata()
      const info = metadata.info as {
        Title?: string
        Author?: string
        Subject?: string
        Creator?: string
        Producer?: string
        CreationDate?: string
        ModDate?: string
      }
      const pageCount = pdf.numPages

      return {
        title: info?.Title,
        author: info?.Author,
        subject: info?.Subject,
        creator: info?.Creator,
        producer: info?.Producer,
        creationDate: info?.CreationDate ? new Date(info.CreationDate) : undefined,
        modificationDate: info?.ModDate ? new Date(info.ModDate) : undefined,
        pageCount,
      }
    } catch (error) {
      logger.warn('메타데이터 추출 실패', error)
      return {
        pageCount: pdf.numPages,
      }
    }
  }

  private async processPage(page: pdfjsLib.PDFPageProxy, pageNumber: number): Promise<PDFPage> {
    try {
      // 페이지 뷰포트 정보 가져오기
      const viewport = page.getViewport({ scale: 1.0 })

      // 텍스트 콘텐츠 추출
      const textContent = await page.getTextContent()
      const text = this.extractTextFromContent(textContent)

      // 이미지 추출
      const images = await this.extractImagesFromPage(page, pageNumber)

      return {
        pageNumber,
        text,
        images,
        width: viewport.width,
        height: viewport.height,
      }
    } catch (error) {
      logger.error(`페이지 ${pageNumber} 처리 중 오류`, error)
      return {
        pageNumber,
        text: '',
        images: [],
        width: 0,
        height: 0,
      }
    }
  }

  private async extractImagesFromPage(
    page: pdfjsLib.PDFPageProxy,
    pageNumber: number
  ): Promise<string[]> {
    try {
      const images: string[] = []

      // 페이지의 리소스를 가져옴
      const operatorList = await page.getOperatorList()

      // 이미지 리소스 필터링
      for (let i = 0; i < operatorList.fnArray.length; i++) {
        const fn = operatorList.fnArray[i]

        // 'paintImageXObject' 함수는 이미지를 의미
        if (fn === pdfjsLib.OPS.paintImageXObject) {
          const name = operatorList.argsArray[i]?.[0]

          if (name && typeof name === 'string') {
            // 이미지 리소스 정보 추출
            const imageInfo = await this.getImageResource(page, name)
            if (imageInfo) {
              images.push(imageInfo)
            }
          }
        }
      }

      return images
    } catch (error) {
      logger.error(`페이지 ${pageNumber} 이미지 추출 중 오류`, error)
      return []
    }
  }

  private async getImageResource(
    page: pdfjsLib.PDFPageProxy,
    imageName: string
  ): Promise<string | null> {
    try {
      // Canvas를 생성하여 이미지 렌더링
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')

      if (!ctx) {
        throw new Error('Canvas 컨텍스트 생성 실패')
      }

      // 페이지의 리소스에서 이미지 정보 추출
      const operatorList = await page.getOperatorList()

      // 이미지 리소스를 찾아서 Canvas에 렌더링
      for (let i = 0; i < operatorList.fnArray.length; i++) {
        const fn = operatorList.fnArray[i]

        // 'paintImageXObject' 함수는 이미지를 의미
        if (fn === pdfjsLib.OPS.paintImageXObject) {
          const name = operatorList.argsArray[i]?.[0]

          if (name === imageName) {
            // 이미지의 바운딩 박스 정보 추출
            const width = operatorList.argsArray[i]?.[3] || 1
            const height = operatorList.argsArray[i]?.[4] || 1

            // Canvas 크기 설정
            canvas.width = width
            canvas.height = height

            // 이미지를 Canvas에 렌더링
            await page.render({
              canvas: canvas,
              viewport: page.getViewport({ scale: 1.0 }),
            }).promise

            // Canvas를 이미지 데이터로 변환
            const imageData = canvas.toDataURL('image/png', 0.8)

            return imageData
          }
        }
      }

      // 이미지를 찾지 못한 경우 null 반환
      return null
    } catch (error) {
      logger.error(`이미지 리소스 추출 중 오류`, error)
      return null
    }
  }

  private extractTextFromContent(textContent: TextContent): string {
    try {
      if (!textContent.items || textContent.items.length === 0) {
        return ''
      }

      // TextItem 타입 가드
      const isTextItem = (item: unknown): item is { str: string; transform: number[] } => {
        return (
          typeof item === 'object' &&
          item !== null &&
          'str' in item &&
          'transform' in item &&
          typeof (item as { str: unknown }).str === 'string' &&
          Array.isArray((item as { transform: unknown }).transform)
        )
      }

      // 텍스트 항목들을 y 좌표 기준으로 정렬 (위에서 아래로)
      const items = textContent.items
        .filter(isTextItem)
        .filter(item => (item as { str: string; transform: number[] }).str.trim().length > 0)
        .sort((a, b) => {
          const aY = (a as { str: string; transform: number[] }).transform[5] || 0
          const bY = (b as { str: string; transform: number[] }).transform[5] || 0
          return bY - aY // y 좌표가 큰 것이 위쪽 (일반적인 좌표계)
        })

      if (items.length === 0) {
        return ''
      }

      // 줄 단위로 그룹화
      const lines: string[] = []
      let currentLine = ''
      let currentY = (items[0] as { str: string; transform: number[] }).transform[5] || 0
      const lineThreshold = 5 // 같은 줄로 간주할 y 좌표 차이

      for (const item of items) {
        const itemY = (item as { str: string; transform: number[] }).transform[5] || 0
        const itemText = (item as { str: string; transform: number[] }).str || ''

        // y 좌표가 크게 바뀌면 새로운 줄
        if (Math.abs(itemY - currentY) > lineThreshold) {
          if (currentLine.trim()) {
            lines.push(currentLine.trim())
          }
          currentLine = itemText
          currentY = itemY
        } else {
          // 같은 줄에 추가 (x 좌표 고려)
          const itemX = (item as { str: string; transform: number[] }).transform[4] || 0
          if (currentLine && itemX > 50) {
            // 적절한 간격
            currentLine += ' ' + itemText
          } else {
            currentLine += itemText
          }
        }
      }

      // 마지막 줄 추가
      if (currentLine.trim()) {
        lines.push(currentLine.trim())
      }

      // 줄바꿈으로 연결
      return lines.join('\n')
    } catch (error) {
      logger.error('텍스트 추출 중 오류', error)
      return ''
    }
  }

  // 파일 유효성 검사
  validatePDFFile(file: File): { valid: boolean; error?: string } {
    // 파일 크기 검사 (300MB 제한)
    const maxSize = 300 * 1024 * 1024 // 300MB
    if (file.size > maxSize) {
      return {
        valid: false,
        error: '파일 크기가 너무 큽니다. 최대 300MB까지 지원됩니다.',
      }
    }

    // 파일 형식 검사
    if (file.type !== 'application/pdf') {
      return {
        valid: false,
        error: 'PDF 파일만 지원됩니다.',
      }
    }

    // 파일 이름 검사
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return {
        valid: false,
        error: 'PDF 파일 확장자가 필요합니다.',
      }
    }

    return { valid: true }
  }

  // 스캔본 PDF 감지 로직
  detectScannedPDF(result: PDFProcessingResult): { isScanned: boolean; confidence: number } {
    try {
      const totalTextLength = result.totalTextLength
      const totalPages = result.pages.length
      const totalImages = result.totalImages

      // 페이지당 평균 텍스트 길이 계산
      const avgTextLengthPerPage = totalPages > 0 ? totalTextLength / totalPages : 0

      // 이미지 비율 계산
      const imageRatio = totalPages > 0 ? totalImages / totalPages : 0

      // 스캔본 판단 기준:
      // 1. 페이지당 텍스트 길이가 매우 적음 (100자 미만)
      // 2. 이미지 비율이 높음 (0.5 이상)
      // 3. 전체 텍스트 길이가 매우 적음 (1000자 미만)

      let isScanned = false
      let confidence = 0

      if (avgTextLengthPerPage < 100 && imageRatio > 0.5) {
        isScanned = true
        confidence = Math.min(1, (100 - avgTextLengthPerPage) / 100 + imageRatio)
      } else if (totalTextLength < 1000 && totalImages > 5) {
        isScanned = true
        confidence = Math.min(0.8, totalImages / 10)
      }

      logger.info('스캔본 PDF 감지 결과', {
        isScanned,
        confidence: Math.round(confidence * 100),
        avgTextLengthPerPage: Math.round(avgTextLengthPerPage),
        imageRatio,
      })

      return {
        isScanned,
        confidence: Math.round(confidence * 100) / 100,
      }
    } catch (error) {
      logger.error('스캔본 감지 중 오류', error)
      return { isScanned: false, confidence: 0 }
    }
  }

  // PDF 전처리 (OCR이 필요한 경우)
  async preprocessPDFForOCR(file: File): Promise<Blob> {
    try {
      logger.info('PDF 전처리 시작', { fileName: file.name })

      // PDF.js를 사용하여 문서 로드
      const arrayBuffer = await file.arrayBuffer()
      const pdfData = new Uint8Array(arrayBuffer)

      const pdf = await pdfjsLib.getDocument({
        data: pdfData,
        disableFontFace: false,
        useSystemFonts: true,
      }).promise

      // 각 페이지를 이미지로 변환
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')

      if (!ctx) {
        throw new Error('Canvas 컨텍스트 생성 실패')
      }

      const imagePromises = []

      for (let i = 1; i <= pdf.numPages; i++) {
        const pagePromise = (async () => {
          const page = await pdf.getPage(i)
          const viewport = page.getViewport({ scale: 2.0 }) // 고해상도로 변환

          canvas.width = viewport.width
          canvas.height = viewport.height

          await page.render({
            canvas: canvas,
            viewport: viewport,
          }).promise

          // Canvas를 이미지로 변환
          const imageData = canvas.toDataURL('image/png', 0.8)

          return {
            pageNumber: i,
            imageData,
          }
        })()

        imagePromises.push(pagePromise)
      }

      const pageImages = await Promise.all(imagePromises)

      logger.info('PDF 전처리 완료', {
        totalPages: pageImages.length,
        processedPages: pageImages.filter(img => img.imageData).length,
      })

      // 전처리된 이미지 데이터를 반환 (실제 구현에서는 Blob로 변환)
      return new Blob([JSON.stringify(pageImages)], { type: 'application/json' })
    } catch (error) {
      logger.error('PDF 전처리 중 오류', error)
      throw new Error(
        `PDF 전처리 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
      )
    }
  }
}

// 싱글톤 인스턴스
export const pdfProcessor = new PDFProcessor()
