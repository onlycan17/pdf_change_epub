import { supabase } from './supabase'
import { logger } from '../utils/logger'

export interface UploadFile {
  id: string
  name: string
  size: number
  type: string
  url: string
  uploadedAt: Date
}

export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
}

export interface UploadOptions {
  maxFileSize?: number
  allowedTypes?: string[]
  onProgress?: (progress: UploadProgress) => void
}

export class FileUploadService {
  private static instance: FileUploadService
  private maxFileSize = 50 * 1024 * 1024 // 50MB 기본값

  private constructor() {}

  static getInstance(): FileUploadService {
    if (!FileUploadService.instance) {
      FileUploadService.instance = new FileUploadService()
    }
    return FileUploadService.instance
  }

  async uploadFile(file: File, options: UploadOptions = {}): Promise<UploadFile> {
    try {
      const maxSize = options.maxFileSize || this.maxFileSize

      // 파일 크기 검증
      if (file.size > maxSize) {
        throw new Error(
          `파일 크기가 너무 큽니다. 최대 ${maxSize / (1024 * 1024)}MB까지 가능합니다.`
        )
      }

      // 파일 형식 검증
      if (options.allowedTypes && options.allowedTypes.length > 0) {
        const fileExtension = file.name.split('.').pop()?.toLowerCase()
        const isAllowed = options.allowedTypes.some(type => {
          if (type.startsWith('.')) {
            return fileExtension === type.slice(1)
          }
          return file.type.includes(type)
        })

        if (!isAllowed) {
          throw new Error(
            `허용되지 않는 파일 형식입니다. 허용된 형식: ${options.allowedTypes.join(', ')}`
          )
        }
      }

      // 파일명 생성 (중복 방지)
      const timestamp = Date.now()
      const sanitizedFileName = file.name.replace(/[^a-zA-Z0-9.-]/g, '_')
      const fileName = `${timestamp}_${sanitizedFileName}`

      // 업로드 진행률 추적
      const uploadPromise = supabase.storage.from('pdf-files').upload(fileName, file, {
        cacheControl: '3600',
        upsert: false,
      })

      // 진행률 모니터링 (간단한 구현)
      if (options.onProgress) {
        const totalSize = file.size
        let loaded = 0

        // 시뮬레이션을 위한 진행률 업데이트
        const progressInterval = setInterval(() => {
          loaded += totalSize / 10
          if (loaded >= totalSize) {
            loaded = totalSize
            clearInterval(progressInterval)
          }

          options.onProgress!({
            loaded,
            total: totalSize,
            percentage: Math.round((loaded / totalSize) * 100),
          })
        }, 200)
      }

      const { data, error } = await uploadPromise

      if (error) {
        throw new Error(`파일 업로드 실패: ${error.message}`)
      }

      // 업로드된 파일의 공개 URL 가져오기
      const {
        data: { publicUrl },
      } = supabase.storage.from('pdf-files').getPublicUrl(data.path)

      return {
        id: data.id || `${Date.now()}`,
        name: file.name,
        size: file.size,
        type: file.type,
        url: publicUrl,
        uploadedAt: new Date(),
      }
    } catch (error) {
      logger.error('파일 업로드 중 오류 발생:', error)
      throw error
    }
  }

  async uploadMultipleFiles(files: File[], options: UploadOptions = {}): Promise<UploadFile[]> {
    const uploadPromises = files.map(file => this.uploadFile(file, options))
    return Promise.all(uploadPromises)
  }

  async deleteFile(fileId: string): Promise<void> {
    try {
      const { error } = await supabase.storage.from('pdf-files').remove([fileId])

      if (error) {
        throw new Error(`파일 삭제 실패: ${error.message}`)
      }
    } catch (error) {
      logger.error('파일 삭제 중 오류 발생:', error)
      throw error
    }
  }

  validatePDF(file: File): boolean {
    return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes'

    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
}

export const fileUploadService = FileUploadService.getInstance()
