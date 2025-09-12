import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/common'
import { AlertTriangle, Home, RefreshCw, FileText } from 'lucide-react'

interface ErrorPageProps {
  error?: string
  code?: number | string
}

const ErrorPage: React.FC<ErrorPageProps> = ({ error, code }) => {
  const navigate = useNavigate()

  const handleGoHome = () => {
    navigate('/')
  }

  const handleRefresh = () => {
    window.location.reload()
  }

  const getErrorMessage = (errorCode?: number | string) => {
    if (!errorCode) return '알 수 없는 오류가 발생했습니다.'

    switch (errorCode) {
      case 404:
        return '요청하신 페이지를 찾을 수 없습니다.'
      case 500:
        return '서버 내부 오류가 발생했습니다.'
      case 'NETWORK_ERROR':
        return '네트워크 연결에 문제가 있습니다.'
      case 'FILE_TOO_LARGE':
        return '파일 크기가 너무 큽니다.'
      case 'INVALID_FILE':
        return '유효하지 않은 파일 형식입니다.'
      case 'CONVERSION_FAILED':
        return '파일 변환에 실패했습니다.'
      default:
        return error || '오류가 발생했습니다.'
    }
  }

  const getErrorIcon = () => {
    if (code === 404) return <FileText className="w-16 h-16" />
    if (code === 500) return <AlertTriangle className="w-16 h-16" />
    if (code === 'NETWORK_ERROR') return <RefreshCw className="w-16 h-16" />
    return <AlertTriangle className="w-16 h-16" />
  }

  const getErrorColor = () => {
    if (code === 404) return 'text-blue-500'
    if (code === 500) return 'text-red-500'
    if (code === 'NETWORK_ERROR') return 'text-yellow-500'
    return 'text-red-500'
  }

  const getErrorBgColor = () => {
    if (code === 404) return 'bg-blue-50 dark:bg-blue-900/20'
    if (code === 500) return 'bg-red-50 dark:bg-red-900/20'
    if (code === 'NETWORK_ERROR') return 'bg-yellow-50 dark:bg-yellow-900/20'
    return 'bg-red-50 dark:bg-red-900/20'
  }

  const errorMessage = getErrorMessage(code)
  const errorIconColor = getErrorColor()
  const bgColor = getErrorBgColor()

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* 에러 아이콘 */}
        <div className="flex justify-center mb-8">
          <div className={`${bgColor} rounded-full p-6 shadow-lg`}>{getErrorIcon()}</div>
        </div>

        {/* 에러 메시지 */}
        <div className="text-center mb-8">
          {code && <h1 className={`text-6xl font-bold ${errorIconColor} mb-4`}>{code}</h1>}
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            {code ? '오류가 발생했습니다' : '죄송합니다'}
          </h2>
          <p className="text-gray-600 dark:text-slate-400 text-lg">{errorMessage}</p>
        </div>

        {/* 버튼 그룹 */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            onClick={handleGoHome}
            variant="primary"
            className="w-full sm:w-auto px-6 py-3 flex items-center justify-center"
          >
            <Home className="w-5 h-5 mr-2" />
            홈으로 돌아가기
          </Button>

          <Button
            onClick={handleRefresh}
            variant="secondary"
            className="w-full sm:w-auto px-6 py-3 flex items-center justify-center"
          >
            <RefreshCw className="w-5 h-5 mr-2" />
            새로고침
          </Button>
        </div>

        {/* 추가 정보 */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500 dark:text-slate-400">
            문제가 지속될 경우 관리자에게 문의해 주세요.
          </p>
        </div>

        {/* 디버깅 정보 (개발 환경에서만 표시) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-8 p-4 bg-gray-100 dark:bg-slate-800 rounded-lg">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-300 mb-2">
              디버깅 정보
            </h3>
            <div className="text-xs text-gray-600 dark:text-slate-400 space-y-1">
              <p>오류 코드: {code || 'N/A'}</p>
              <p>메시지: {errorMessage}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ErrorPage
