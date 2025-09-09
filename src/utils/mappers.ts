import type { ConversionResult } from '../types/conversion'

interface DBConversionRow {
  id: string
  original_file_id: string
  original_file_name: string
  converted_file_url: string
  converted_file_name: string
  format: string
  size: number
  created_at: string
  expires_at: string
}

export function mapConversionRowToResult(row: DBConversionRow): ConversionResult {
  return {
    id: row.id,
    originalFileId: row.original_file_id,
    originalFileName: row.original_file_name,
    convertedFileUrl: row.converted_file_url,
    convertedFileName: row.converted_file_name,
    format: row.format,
    size: row.size,
    createdAt: new Date(row.created_at),
    expiresAt: new Date(row.expires_at),
  }
}
