export interface ConversionResult {
  id: string
  originalFileId: string
  originalFileName: string
  convertedFileUrl: string
  convertedFileName: string
  format: string
  size: number
  createdAt: Date
  expiresAt: Date
}
