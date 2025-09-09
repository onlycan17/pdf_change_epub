import { logger } from './logger'

function isErrorWithMessage(e: unknown): e is { message: string } {
  return (
    typeof e === 'object' &&
    e !== null &&
    'message' in e &&
    typeof (e as { message?: unknown }).message === 'string'
  )
}

// 사용자 노출용 에러 메시지 변환 유틸
export function getUserMessage(error: unknown, fallback = '알 수 없는 오류가 발생했습니다.') {
  if (isErrorWithMessage(error)) {
    const msg = error.message
    if (msg.length > 200) return fallback
    return msg
  }
  return fallback
}

export function logAndGetUserMessage(error: unknown, fallback?: string) {
  logger.error(error)
  return getUserMessage(error, fallback)
}
