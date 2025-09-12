import React, { useState, useCallback } from 'react'
import { ConversionOptions as ConversionOptionsType } from '../services'

interface ConversionOptionsProps {
  options: ConversionOptionsType
  onChange: (options: ConversionOptionsType) => void
  disabled?: boolean
}

export const ConversionOptions: React.FC<ConversionOptionsProps> = ({
  options,
  onChange,
  disabled = false,
}) => {
  const [localOptions, setLocalOptions] = useState<ConversionOptionsType>({
    useOCR: false,
    ocrLanguage: 'auto',
    markdownOptions: {
      preserveFormatting: true,
      includePageNumbers: true,
      headingDetection: true,
      listDetection: true,
      tableDetection: true,
    },
    ...options,
  })

  const handleOptionChange = useCallback(
    (key: string, value: boolean | string) => {
      const newOptions = { ...localOptions, [key]: value }
      setLocalOptions(newOptions)
      onChange(newOptions)
    },
    [localOptions, onChange]
  )

  const handleMarkdownOptionChange = useCallback(
    (key: string, value: boolean) => {
      const newOptions = {
        ...localOptions,
        markdownOptions: {
          ...localOptions.markdownOptions,
          [key]: value,
        },
      }
      setLocalOptions(newOptions)
      onChange(newOptions)
    },
    [localOptions, onChange]
  )

  return (
    <div className="space-y-6 p-6 bg-white rounded-lg border">
      <h3 className="text-lg font-semibold text-gray-900">변환 옵션</h3>

      {/* OCR 옵션 */}
      <div className="space-y-2">
        <div className="flex items-center">
          <input
            type="checkbox"
            id="useOCR"
            checked={localOptions.useOCR}
            onChange={e => handleOptionChange('useOCR', e.target.checked)}
            disabled={disabled}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="useOCR" className="ml-2 block text-sm text-gray-700">
            OCR(광학 문자 인식) 사용
          </label>
        </div>
        <p className="text-xs text-gray-500 ml-6">
          스캔된 PDF나 이미지가 포함된 문서에서 텍스트를 추출합니다
        </p>
      </div>

      {/* 마크다운 옵션 */}
      <div className="space-y-4">
        <h4 className="text-md font-medium text-gray-800">마크다운 형식 옵션</h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* 서식 유지 */}
          <div className="space-y-2">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="preserveFormatting"
                checked={localOptions.markdownOptions?.preserveFormatting ?? true}
                onChange={e => handleMarkdownOptionChange('preserveFormatting', e.target.checked)}
                disabled={disabled}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="preserveFormatting" className="ml-2 block text-sm text-gray-700">
                서식 유지
              </label>
            </div>
            <p className="text-xs text-gray-500 ml-6">
              원본 문서의 굵은 글씨, 기울임꼴 등 서식을 유지합니다
            </p>
          </div>

          {/* 페이지 번호 포함 */}
          <div className="space-y-2">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="includePageNumbers"
                checked={localOptions.markdownOptions?.includePageNumbers ?? true}
                onChange={e => handleMarkdownOptionChange('includePageNumbers', e.target.checked)}
                disabled={disabled}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="includePageNumbers" className="ml-2 block text-sm text-gray-700">
                페이지 번호 포함
              </label>
            </div>
            <p className="text-xs text-gray-500 ml-6">각 페이지 시작에 페이지 번호를 표시합니다</p>
          </div>

          {/* 제목 감지 */}
          <div className="space-y-2">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="headingDetection"
                checked={localOptions.markdownOptions?.headingDetection ?? true}
                onChange={e => handleMarkdownOptionChange('headingDetection', e.target.checked)}
                disabled={disabled}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="headingDetection" className="ml-2 block text-sm text-gray-700">
                제목 감지
              </label>
            </div>
            <p className="text-xs text-gray-500 ml-6">
              문서의 제목을 자동으로 감지하여 마크다운 제목으로 변환합니다
            </p>
          </div>

          {/* 목록 감지 */}
          <div className="space-y-2">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="listDetection"
                checked={localOptions.markdownOptions?.listDetection ?? true}
                onChange={e => handleMarkdownOptionChange('listDetection', e.target.checked)}
                disabled={disabled}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="listDetection" className="ml-2 block text-sm text-gray-700">
                목록 감지
              </label>
            </div>
            <p className="text-xs text-gray-500 ml-6">
              글머리 기호와 번호가 있는 목록을 자동으로 감지합니다
            </p>
          </div>

          {/* 테이블 감지 */}
          <div className="space-y-2">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="tableDetection"
                checked={localOptions.markdownOptions?.tableDetection ?? true}
                onChange={e => handleMarkdownOptionChange('tableDetection', e.target.checked)}
                disabled={disabled}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="tableDetection" className="ml-2 block text-sm text-gray-700">
                테이블 감지
              </label>
            </div>
            <p className="text-xs text-gray-500 ml-6">
              표 형식의 데이터를 마크다운 테이블로 변환합니다
            </p>
          </div>

          {/* 이미지 추출 */}
          <div className="space-y-2">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="extractImages"
                checked={false}
                onChange={e => handleMarkdownOptionChange('extractImages', e.target.checked)}
                disabled={true}
                className="h-4 w-4 text-gray-400 focus:ring-gray-300 border-gray-300 rounded"
              />
              <label htmlFor="extractImages" className="ml-2 block text-sm text-gray-400">
                이미지 추출 (준비 중)
              </label>
            </div>
            <p className="text-xs text-gray-400 ml-6">
              PDF의 이미지를 추출하여 마크다운에 포함합니다 (현재 지원되지 않음)
            </p>
          </div>
        </div>
      </div>

      {/* 고급 옵션 */}
      <div className="space-y-4">
        <h4 className="text-md font-medium text-gray-800">고급 옵션</h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* 품질 vs 속도 */}
          <div className="space-y-2">
            <label htmlFor="qualityMode" className="block text-sm font-medium text-gray-700">
              변환 모드
            </label>
            <select
              id="qualityMode"
              value={'balanced'}
              onChange={e => handleOptionChange('qualityMode', e.target.value)}
              disabled={true}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md bg-gray-100"
            >
              <option value="balanced">균형잡힌</option>
            </select>
            <p className="text-xs text-gray-500">
              변환 품질과 속도의 균형을 선택합니다 (현재 균형잡힌 모드만 지원)
            </p>
          </div>

          {/* 언어 설정 */}
          <div className="space-y-2">
            <label htmlFor="language" className="block text-sm font-medium text-gray-700">
              문서 언어
            </label>
            <select
              id="language"
              value={localOptions.ocrLanguage || 'auto'}
              onChange={e => handleOptionChange('ocrLanguage', e.target.value)}
              disabled={disabled}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            >
              <option value="auto">자동 감지</option>
              <option value="ko">한국어</option>
              <option value="en">영어</option>
              <option value="ja">일본어</option>
              <option value="zh">중국어</option>
            </select>
            <p className="text-xs text-gray-500">OCR 및 텍스트 처리를 위한 언어를 선택합니다</p>
          </div>
        </div>
      </div>

      {/* 옵션 초기화 버튼 */}
      <div className="pt-4 border-t">
        <button
          type="button"
          onClick={() => {
            const defaultOptions: ConversionOptionsType = {
              useOCR: false,
              ocrLanguage: 'auto',
              markdownOptions: {
                preserveFormatting: true,
                includePageNumbers: true,
                headingDetection: true,
                listDetection: true,
                tableDetection: true,
              },
            }
            setLocalOptions(defaultOptions)
            onChange(defaultOptions)
          }}
          disabled={disabled}
          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          기본값으로 초기화
        </button>
      </div>
    </div>
  )
}
