import React, { useCallback, useState, useRef } from 'react'
import { usePDFConversion } from '../hooks'
import { ConversionOptions } from '../services'

interface PDFMetadata {
  title?: string
  author?: string
  pageCount: number
  wordCount: number
  processingTime: number
}

interface PDFUploaderProps {
  onConversionComplete?: (markdown: string, metadata: PDFMetadata) => void
  onError?: (error: string) => void
}

export const PDFUploader: React.FC<PDFUploaderProps> = ({ onConversionComplete, onError }) => {
  const { convertPDF, isConverting, progress, result, error, stages } = usePDFConversion()
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleFile = useCallback(
    async (file: File) => {
      // PDF 파일인지 확인
      if (!file.type.includes('pdf')) {
        onError?.('PDF 파일만 업로드 가능합니다.')
        return
      }

      // 파일 크기 확인 (50MB 제한)
      if (file.size > 50 * 1024 * 1024) {
        onError?.('파일 크기는 50MB를 초과할 수 없습니다.')
        return
      }

      setSelectedFile(file)

      const options: ConversionOptions = {
        useOCR: false, // 기본적으로 OCR 비활성화
        ocrLanguage: 'kor', // 한국어 OCR 기본값
        markdownOptions: {
          preserveFormatting: true,
          includePageNumbers: true,
          headingDetection: true,
          listDetection: true,
          tableDetection: true,
        },
      }

      await convertPDF(file, options)

      if (result?.success && result.markdown) {
        // metadata가 undefined일 경우 기본값 제공
        const metadata: PDFMetadata = result.metadata || {
          pageCount: 0,
          wordCount: 0,
          processingTime: 0,
        }
        onConversionComplete?.(result.markdown, metadata)
      } else if (error) {
        onError?.(error)
      }
    },
    [convertPDF, result, error, onConversionComplete, onError]
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setDragActive(false)

      const files = e.dataTransfer.files
      if (files && files[0]) {
        handleFile(files[0])
      }
    },
    [handleFile]
  )

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (files && files[0]) {
        handleFile(files[0])
      }
    },
    [handleFile]
  )

  const handleRetry = useCallback(() => {
    if (selectedFile) {
      handleFile(selectedFile)
    }
  }, [selectedFile, handleFile])

  const handleClear = () => {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 ${
          dragActive
            ? 'border-blue-500 bg-blue-50 shadow-lg transform scale-105'
            : 'border-gray-300 hover:border-gray-400 hover:shadow-md'
        } ${isConverting ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${
          selectedFile ? 'border-green-500 bg-green-50' : ''
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileInput}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={isConverting}
        />

        <div className="space-y-4">
          <div
            className={`mx-auto w-12 h-12 transition-colors ${
              selectedFile ? 'text-green-500' : 'text-gray-400'
            }`}
          >
            <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>

          <div className="space-y-2">
            <p
              className={`text-lg font-medium transition-colors ${
                selectedFile ? 'text-green-700' : 'text-gray-700'
              }`}
            >
              {isConverting
                ? '변환 중...'
                : selectedFile
                  ? `선택된 파일: ${selectedFile.name}`
                  : 'PDF 파일을 드래그 앤 드롭하거나 클릭하여 선택'}
            </p>
            <p className="text-sm text-gray-500">
              {selectedFile
                ? `파일 크기: ${(selectedFile.size / 1024 / 1024).toFixed(2)}MB`
                : '최대 50MB 크기의 PDF 파일만 지원됩니다'}
            </p>
          </div>
        </div>
      </div>

      {/* 진행 상황 표시 */}
      {isConverting && (
        <div className="mt-6 space-y-4 animate-fade-in">
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600 font-medium">
              {stages.length > 0 ? stages[stages.length - 1].message : '변환 준비 중...'}
            </p>
            <p className="text-xs text-gray-500 mt-1">{progress}% 완료</p>
          </div>

          {/* 단계별 진행 상황 */}
          {stages.length > 0 && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
              <h4 className="text-sm font-medium text-gray-700 mb-3">변환 단계</h4>
              <div className="space-y-3">
                {stages.map((stage, index) => (
                  <div
                    key={index}
                    className={`flex items-center text-sm ${
                      index === stages.length - 1
                        ? 'text-blue-600 font-medium animate-pulse'
                        : index < stages.length - 1
                          ? 'text-green-600'
                          : 'text-gray-500'
                    }`}
                  >
                    <div
                      className={`w-3 h-3 rounded-full mr-3 flex items-center justify-center ${
                        index === stages.length - 1
                          ? 'bg-blue-600'
                          : index < stages.length - 1
                            ? 'bg-green-500'
                            : 'bg-gray-300'
                      }`}
                    >
                      {index < stages.length - 1 && (
                        <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </div>
                    {stage.message}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 결과 표시 */}
      {result?.success && result.markdown && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg animate-fade-in">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-green-800">변환 완료</h4>
            <div className="flex space-x-2">
              <button
                onClick={handleClear}
                className="px-3 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
              >
                새 파일 선택
              </button>
            </div>
          </div>
          <div className="text-sm text-green-700 space-y-2">
            <div className="flex justify-between">
              <span>페이지 수:</span>
              <span className="font-medium">{result.metadata?.pageCount || 0}</span>
            </div>
            <div className="flex justify-between">
              <span>단어 수:</span>
              <span className="font-medium">
                {result.metadata?.wordCount?.toLocaleString() || 0}
              </span>
            </div>
            <div className="flex justify-between">
              <span>처리 시간:</span>
              <span className="font-medium">
                {result.metadata?.processingTime
                  ? `${(result.metadata.processingTime / 1000).toFixed(2)}초`
                  : '측정 불가'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 오류 표시 */}
      {error && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg animate-fade-in">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-red-800">변환 실패</h4>
            <div className="flex space-x-2">
              <button
                onClick={handleRetry}
                className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
              >
                재시도
              </button>
              <button
                onClick={handleClear}
                className="px-3 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
              >
                새 파일 선택
              </button>
            </div>
          </div>
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* 애니메이션 스타일 */}
      <style>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
      `}</style>
    </div>
  )
}
