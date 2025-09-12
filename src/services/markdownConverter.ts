import { logger } from '../utils/logger'
import { PDFPage } from './pdfProcessor'

export interface MarkdownOptions {
  preserveFormatting?: boolean
  includePageNumbers?: boolean
  headingDetection?: boolean
  listDetection?: boolean
  tableDetection?: boolean
}

export interface MarkdownConversionResult {
  markdown: string
  pageCount: number
  wordCount: number
  headingCount: number
  listCount: number
  tableCount: number
}

export class MarkdownConverter {
  constructor() {}

  convertToMarkdown(pages: PDFPage[], options: MarkdownOptions = {}): MarkdownConversionResult {
    try {
      logger.info('마크다운 변환 시작', { pageCount: pages.length })

      const startTime = Date.now()
      const {
        includePageNumbers = true,
        headingDetection = true,
        listDetection = true,
        tableDetection = true,
      } = options

      let markdown = ''
      let totalWordCount = 0
      let headingCount = 0
      let listCount = 0
      let tableCount = 0

      pages.forEach((page, index) => {
        if (includePageNumbers) {
          markdown += `\\newpage\n\n`
        }

        // 페이지 텍스트 처리
        const processedText = this.processPageText(page.text, {
          headingDetection,
          listDetection,
          tableDetection,
        })

        markdown += processedText.text
        headingCount += processedText.headingCount
        listCount += processedText.listCount
        tableCount += processedText.tableCount

        // 단어 수 계산
        const words = processedText.text.split(/\s+/).filter(word => word.length > 0)
        totalWordCount += words.length

        // 페이지 구분자 추가
        if (index < pages.length - 1) {
          markdown += '\n\n---\n\n'
        }
      })

      // 전체 문서 구조화
      markdown = this.structureDocument(markdown)

      const processingTime = Date.now() - startTime

      const result: MarkdownConversionResult = {
        markdown,
        pageCount: pages.length,
        wordCount: totalWordCount,
        headingCount,
        listCount,
        tableCount,
      }

      logger.info('마크다운 변환 완료', {
        processingTime,
        pageCount: result.pageCount,
        wordCount: result.wordCount,
        headingCount: result.headingCount,
      })

      return result
    } catch (error) {
      logger.error('마크다운 변환 중 오류', error)
      throw new Error(
        `마크다운 변환 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
      )
    }
  }

  private processPageText(
    text: string,
    options: {
      headingDetection: boolean
      listDetection: boolean
      tableDetection: boolean
    }
  ): {
    text: string
    headingCount: number
    listCount: number
    tableCount: number
  } {
    let processedText = text
    let headingCount = 0
    let listCount = 0
    let tableCount = 0

    // 줄바꿈 정리
    processedText = processedText.replace(/\r\n/g, '\n').replace(/\r/g, '\n')

    // 제목 감지 및 변환
    if (options.headingDetection) {
      const headingResult = this.detectAndConvertHeadings(processedText)
      processedText = headingResult.text
      headingCount = headingResult.headingCount
    }

    // 목록 감지 및 변환
    if (options.listDetection) {
      const listResult = this.detectAndConvertLists(processedText)
      processedText = listResult.text
      listCount = listResult.listCount
    }

    // 표 감지 및 변환
    if (options.tableDetection) {
      const tableResult = this.detectAndConvertTables(processedText)
      processedText = tableResult.text
      tableCount = tableResult.tableCount
    }

    // 문단 구조화
    processedText = this.structureParagraphs(processedText)

    return {
      text: processedText,
      headingCount,
      listCount,
      tableCount,
    }
  }

  private detectAndConvertHeadings(text: string): { text: string; headingCount: number } {
    const lines = text.split('\n')
    let headingCount = 0
    const processedLines: string[] = []

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()

      if (line.length === 0) {
        processedLines.push('')
        continue
      }

      // 제목 패턴 감지
      const headingLevel = this.detectHeadingLevel(line)
      if (headingLevel > 0) {
        processedLines.push('#'.repeat(headingLevel) + ' ' + line)
        headingCount++
      } else {
        processedLines.push(line)
      }
    }

    return {
      text: processedLines.join('\n'),
      headingCount,
    }
  }

  private detectHeadingLevel(line: string): number {
    // 간단한 제목 감지 로직
    const trimmedLine = line.trim()

    // 빈 줄은 제목이 아님
    if (!trimmedLine) {
      return 0
    }

    // 짧은 라인 (50자 이하)이고 대문자가 많은 경우
    if (trimmedLine.length <= 50 && this.getUppercaseRatio(trimmedLine) > 0.3) {
      return 2 // h2로 간주
    }

    // 숫자로 시작하는 라인 (1. Introduction 같은 경우)
    if (/^\d+\.\s+/.test(trimmedLine)) {
      return 2 // h2로 간주
    }

    // 로마 숫자로 시작하는 경우 (I. Introduction, II. Methods 등)
    if (/^[IVXLCDM]+\.\s+/.test(trimmedLine)) {
      return 1 // h1로 간주
    }

    // 챕터, 섹션 등의 키워드가 포함된 경우
    const headingKeywords = [
      'chapter',
      'section',
      'part',
      'introduction',
      'conclusion',
      'summary',
      'abstract',
      'method',
      'result',
      'discussion',
      'reference',
      'appendix',
    ]
    const lowerLine = trimmedLine.toLowerCase()
    if (headingKeywords.some(keyword => lowerLine.includes(keyword))) {
      return 1 // h1로 간주
    }

    // 라인 길이와 구두점 비율로 제목 판단
    if (trimmedLine.length <= 80 && this.getPunctuationRatio(trimmedLine) < 0.1) {
      // 마침표, 쉼표 등이 없고 적절한 길이인 경우
      const words = trimmedLine.split(/\s+/)
      if (words.length >= 2 && words.length <= 10) {
        return 3 // h3로 간주
      }
    }

    return 0 // 제목이 아님
  }

  private getPunctuationRatio(text: string): number {
    const punctuationCount = (text.match(/[.,;:!?]/g) || []).length
    return punctuationCount / text.length
  }

  private getUppercaseRatio(text: string): number {
    const uppercaseCount = (text.match(/[A-Z]/g) || []).length
    return uppercaseCount / text.length
  }

  private detectAndConvertLists(text: string): { text: string; listCount: number } {
    const lines = text.split('\n')
    let listCount = 0
    const processedLines: string[] = []
    let inList = false

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()

      if (line.length === 0) {
        processedLines.push('')
        inList = false
        continue
      }

      // 순서 있는 목록 패턴 감지 (1., 2., 3. 등)
      const orderedListMatch = line.match(/^(\d+)\.\s+(.+)$/)
      if (orderedListMatch) {
        processedLines.push(`${orderedListMatch[1]}. ${orderedListMatch[2]}`)
        listCount++
        inList = true
        continue
      }

      // 순서 없는 목록 패턴 감지 (-, •, *, + 등)
      const unorderedListMatch = line.match(/^([-•*+])\s+(.+)$/)
      if (unorderedListMatch) {
        processedLines.push(`- ${unorderedListMatch[2]}`)
        listCount++
        inList = true
        continue
      }

      // 들여쓰기된 하위 항목 감지
      if (inList && line.startsWith('  ')) {
        processedLines.push(`  - ${line.trim()}`)
        listCount++
        continue
      }

      // 일반 텍스트
      processedLines.push(line)
      inList = false
    }

    return {
      text: processedLines.join('\n'),
      listCount,
    }
  }

  private detectAndConvertTables(text: string): { text: string; tableCount: number } {
    const lines = text.split('\n')
    let tableCount = 0
    const processedLines: string[] = []

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()

      // 파이프(|)로 구분된 텍스트가 있는 경우 표로 간주
      if (line.includes('|') && line.split('|').length >= 3) {
        // 표 헤더 처리
        const cells = line
          .split('|')
          .map(cell => cell.trim())
          .filter(cell => cell.length > 0)
        if (cells.length >= 2) {
          processedLines.push(line)

          // 구분선 추가 (마크다운 표 형식)
          if (i + 1 < lines.length && !lines[i + 1].includes('|')) {
            const separator = cells.map(() => '---').join(' | ')
            processedLines.push(`| ${separator} |`)
          }

          tableCount++
        } else {
          processedLines.push(line)
        }
      } else {
        processedLines.push(line)
      }
    }

    return {
      text: processedLines.join('\n'),
      tableCount,
    }
  }

  private structureParagraphs(text: string): string {
    // 연속된 줄바꿈을 문단 구분으로 변환
    const processed = text.replace(/\n{3,}/g, '\n\n')

    // 문장이 끝나지 않은 줄은 다음 줄과 연결
    const lines = processed.split('\n')
    const resultLines: string[] = []

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()
      const prevLine = resultLines[resultLines.length - 1]

      // 이전 줄이 문장의 끝이 아니고 현재 줄이 짧은 경우 연결
      if (
        prevLine &&
        !prevLine.match(/[.!?]$/) &&
        line.length < 100 &&
        !line.match(/^[-•*+]/) &&
        !line.match(/^\d+\./)
      ) {
        resultLines[resultLines.length - 1] = prevLine + ' ' + line
      } else {
        resultLines.push(line)
      }
    }

    return resultLines.join('\n')
  }

  private structureDocument(markdown: string): string {
    // 문서 시작에 제목 추가 (첫 번째 제목이 있다면)
    const lines = markdown.split('\n')
    const firstHeadingIndex = lines.findIndex(line => line.startsWith('#'))

    if (firstHeadingIndex === -1) {
      // 제목이 없으면 문서 제목 추가
      return '# 변환된 문서\n\n' + markdown
    }

    return markdown
  }

  // 마크다운 유효성 검사
  validateMarkdown(markdown: string): { valid: boolean; error?: string } {
    try {
      if (!markdown || markdown.trim().length === 0) {
        return {
          valid: false,
          error: '마크다운 내용이 비어있습니다.',
        }
      }

      if (markdown.length > 1000000) {
        return {
          valid: false,
          error: '마크다운이 너무 깁니다. 최대 1MB까지 지원됩니다.',
        }
      }

      return { valid: true }
    } catch (error) {
      logger.error('마크다운 유효성 검사 중 오류', error)
      return {
        valid: false,
        error: '마크다운 유효성 검사 실패',
      }
    }
  }
}

// 싱글톤 인스턴스
export const markdownConverter = new MarkdownConverter()
