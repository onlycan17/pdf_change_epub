import React, { useCallback, useState } from 'react'
import { Upload, X, CloudUpload, CheckCircle, AlertCircle, Sparkles } from 'lucide-react'

interface FileUploadProps {
  onFileSelect: (file: File) => void
  accept?: string
  maxSize?: number // MB 단위
  disabled?: boolean
  className?: string
}

const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  accept = '.pdf',
  maxSize = 10,
  disabled = false,
  className = '',
}) => {
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState<string>('')
  const [isProcessing, setIsProcessing] = useState(false)

  const validateFile = useCallback(
    (file: File): boolean => {
      // 파일 형식 검증
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        setError('PDF 파일만 업로드할 수 있습니다.')
        return false
      }

      // 파일 크기 검증
      const fileSizeMB = file.size / (1024 * 1024)
      if (fileSizeMB > maxSize) {
        setError(`파일 크기는 ${maxSize}MB 이하여야 합니다.`)
        return false
      }

      setError('')
      return true
    },
    [maxSize]
  )

  const handleFileSelect = useCallback(
    (file: File) => {
      if (validateFile(file)) {
        setSelectedFile(file)
        setIsProcessing(true)

        // 시레이션 처리 시간
        setTimeout(() => {
          setIsProcessing(false)
          onFileSelect(file)
        }, 1500)
      }
    },
    [onFileSelect, validateFile]
  )

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      setIsDragOver(false)

      if (disabled) return

      const files = Array.from(e.dataTransfer.files)
      if (files.length > 0) {
        handleFileSelect(files[0])
      }
    },
    [handleFileSelect, disabled]
  )

  const handleDragOver = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      if (!disabled) {
        setIsDragOver(true)
      }
    },
    [disabled]
  )

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (files && files.length > 0) {
        handleFileSelect(files[0])
      }
    },
    [handleFileSelect]
  )

  const handleRemoveFile = useCallback(() => {
    setSelectedFile(null)
    setError('')
    setIsProcessing(false)
  }, [])

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className={`w-full ${className}`}>
      {!selectedFile ? (
        <div
          className={`relative group cursor-pointer transition-all duration-500 ${
            isDragOver && !disabled
              ? 'scale-105'
              : disabled
                ? 'opacity-50 cursor-not-allowed'
                : 'hover:scale-105'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => !disabled && document.getElementById('file-input')?.click()}
        >
          <div
            className={`
            relative overflow-hidden rounded-3xl border-2 border-dashed p-8 lg:p-12 text-center
            transition-all duration-300
            ${
              isDragOver && !disabled
                ? 'border-blue-400 bg-blue-50/50 dark:bg-blue-900/20 shadow-2xl shadow-blue-500/20'
                : disabled
                  ? 'border-gray-300 bg-gray-100 dark:bg-gray-800'
                  : 'border-slate-300 dark:border-slate-600 hover:border-blue-400 dark:hover:border-blue-500 bg-white/50 dark:bg-slate-800/50 hover:shadow-2xl hover:shadow-blue-500/10'
            }
          `}
          >
            {/* Background Effects */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-purple-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_50%_50%,rgba(59,130,246,0.1),transparent_70%)] opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

            <div className="relative z-10">
              {/* Upload Icon with Animation */}
              <div className="relative mb-6">
                <div
                  className={`
                  w-20 h-20 mx-auto rounded-3xl flex items-center justify-center
                  transition-all duration-500 group-hover:scale-110
                  ${
                    isDragOver
                      ? 'bg-gradient-to-br from-blue-500 to-purple-600 shadow-2xl shadow-blue-500/50'
                      : 'bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-700 dark:to-slate-600 group-hover:from-blue-500 group-hover:to-purple-600 group-hover:shadow-2xl group-hover:shadow-blue-500/50'
                  }
                `}
                >
                  {isDragOver ? (
                    <CloudUpload className="w-10 h-10 text-white animate-bounce" />
                  ) : (
                    <Upload className="w-10 h-10 text-slate-600 dark:text-slate-300 group-hover:text-white transition-colors" />
                  )}
                </div>

                {/* Floating particles effect */}
                <div className="absolute inset-0 -z-10">
                  {[...Array(6)].map((_, i) => (
                    <div
                      key={i}
                      className={`
                        absolute w-2 h-2 bg-blue-400 rounded-full opacity-0
                        group-hover:opacity-100 group-hover:animate-pulse
                        transition-all duration-1000
                      `}
                      style={{
                        top: `${20 + Math.sin(i * 60) * 30}%`,
                        left: `${50 + Math.cos(i * 60) * 40}%`,
                        animationDelay: `${i * 0.2}s`,
                      }}
                    />
                  ))}
                </div>
              </div>

              {/* Main Text */}
              <div className="space-y-3">
                <h3
                  className={`
                  text-xl lg:text-2xl font-bold transition-colors duration-300
                  ${
                    isDragOver
                      ? 'text-blue-600 dark:text-blue-400'
                      : 'text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400'
                  }
                `}
                >
                  {isDragOver ? 'Drop your file here!' : 'Drop PDF file here'}
                </h3>

                <p className="text-slate-600 dark:text-slate-300 group-hover:text-slate-700 dark:group-hover:text-slate-200 transition-colors">
                  or click to browse files
                </p>

                <div className="flex items-center justify-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                  <Sparkles className="w-4 h-4" />
                  <span>Maximum file size: {maxSize}MB</span>
                </div>
              </div>

              {/* Upload Button */}
              <div className="mt-8">
                <button
                  className={`
                    btn group relative overflow-hidden
                    ${
                      isDragOver
                        ? 'btn-primary'
                        : 'btn-outline border-slate-300 dark:border-slate-600 hover:border-blue-500'
                    }
                  `}
                  onClick={e => {
                    e.stopPropagation()
                    !disabled && document.getElementById('file-input')?.click()
                  }}
                  disabled={disabled}
                >
                  <span className="relative z-10 flex items-center gap-2">
                    <Upload className="w-4 h-4" />
                    Choose File
                  </span>

                  {/* Button shine effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
                </button>
              </div>

              {/* Hidden file input */}
              <input
                id="file-input"
                type="file"
                accept={accept}
                onChange={handleFileInputChange}
                disabled={disabled}
                className="hidden"
              />
            </div>
          </div>
        </div>
      ) : (
        <div className="card hover-lift">
          <div className="card-body p-6">
            {isProcessing ? (
              <div className="text-center py-8">
                <div className="loading-spinner mx-auto mb-4"></div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                  Processing your file...
                </h3>
                <p className="text-slate-600 dark:text-slate-300">Preparing for conversion</p>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center">
                    <CheckCircle className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {formatFileSize(selectedFile.size)}
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleRemoveFile}
                  className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-all"
                  disabled={disabled}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}
    </div>
  )
}

export default FileUpload
