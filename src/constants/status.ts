export const CONVERSION_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
} as const

export type ConversionStatus = (typeof CONVERSION_STATUS)[keyof typeof CONVERSION_STATUS]
