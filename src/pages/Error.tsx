import React from 'react'
import { useNavigate, useRouteError } from 'react-router-dom'
import { Button } from '../components/common'
import { AlertTriangle, Home, RefreshCw, Mail } from 'lucide-react'

interface ErrorPageProps {
  error?: {
    message?: string
    code?: string
  }
}

const Error: React.FC<ErrorPageProps> = ({ error: propError }) => {
  const navigate = useNavigate()
  const routeError = useRouteError() as { message?: string; code?: string }
  const error = propError || routeError || {}

  const getErrorDetails = () => {
    const errorCode = error.code || 'UNKNOWN_ERROR'
    const errorMessage = error.message || '알 수 없는 오류가 발생했습니다.'

    const errorDetails: Record<string, { title: string; message: string; solution: string }> = {
      FILE_TOO_LARGE: {
        title: '파일 크기 초과',
        message: '업로드하신 파일이 허용된 최대 크기를 초과합니다.',
        solution: '파일 크기를 줄이거나 프리미엄 플랜으로 업그레이드하세요.',
      },
      INVALID_FILE_TYPE: {
        title: '잘못된 파일 형식',
        message: 'PDF 파일만 업로드할 수 있습니다.',
        solution: 'PDF 형식의 파일을 선택해주세요.',
      },
      CONVERSION_FAILED: {
        title: '변환 실패',
        message: '파일 변환 중 오류가 발생했습니다.',
        solution: '파일이 손상되었는지 확인하고 다시 시도하세요.',
      },
      NETWORK_ERROR: {
        title: '네트워크 오류',
        message: '인터넷 연결을 확인할 수 없습니다.',
        solution: '네트워크 연결을 확인하고 다시 시도하세요.',
      },
      AUTHENTICATION_ERROR: {
        title: '인증 오류',
        message: '로그인이 필요하거나 세션이 만료되었습니다.',
        solution: '다시 로그인해주세요.',
      },
      PREMIUM_REQUIRED: {
        title: '프리미엄 기능 필요',
        message: '이 기능은 프리미엄 플랜이 필요합니다.',
        solution: '프리미엄 플랜으로 업그레이드하세요.',
      },
      RATE_LIMIT_EXCEEDED: {
        title: '사용량 초과',
        message: '일일 사용량 제한에 도달했습니다.',
        solution: '내일 다시 시도하거나 프리미엄으로 업그레이드하세요.',
      },
      SERVER_ERROR: {
        title: '서버 오류',
        message: '서버 처리 중 오류가 발생했습니다.',
        solution: '잠시 후 다시 시도하세요. 문제가 지속되면 고객 지원에 문의하세요.',
      },
    }

    return (
      errorDetails[errorCode] || {
        title: '오류 발생',
        message: errorMessage,
        solution: '문제가 지속되면 고객 지원에 문의하세요.',
      }
    )
  }

  const errorDetails = getErrorDetails()

  const handleGoHome = () => {
    navigate('/')
  }

  const handleRetry = () => {
    window.location.reload()
  }

  const handleContactSupport = () => {
    // TODO: 고객 지원 이메일 또는 문의 페이지로 이동
    window.location.href =
      'mailto:support@pdf-to-epub.com?subject=오류 신고&body=오류 코드: ' +
      (error.code || 'UNKNOWN_ERROR')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          {/* 오류 아이콘 */}
          <div className="mb-6">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
              <AlertTriangle className="w-8 h-8 text-red-600" />
            </div>
          </div>

          {/* 오류 제목 */}
          <h1 className="text-2xl font-bold text-gray-900 mb-2">{errorDetails.title}</h1>

          {/* 오류 메시지 */}
          <p className="text-gray-600 mb-4">{errorDetails.message}</p>

          {/* 해결 방법 */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-800">
              <strong>해결 방법:</strong> {errorDetails.solution}
            </p>
          </div>

          {/* 오류 코드 (디버깅용) */}
          <div className="mb-6">
            <p className="text-xs text-gray-500">오류 코드: {error.code || 'UNKNOWN_ERROR'}</p>
          </div>

          {/* 액션 버튼 */}
          <div className="space-y-3">
            <Button onClick={handleGoHome} variant="primary" className="w-full">
              <Home className="w-4 h-4 mr-2" />
              홈으로 돌아가기
            </Button>

            <Button onClick={handleRetry} variant="secondary" className="w-full">
              <RefreshCw className="w-4 h-4 mr-2" />
              다시 시도
            </Button>

            <Button onClick={handleContactSupport} variant="secondary" className="w-full">
              <Mail className="w-4 h-4 mr-2" />
              고객 지원 문의
            </Button>
          </div>
        </div>

        {/* 추가 도움말 */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500 mb-4">도움이 필요하신가요?</p>
          <div className="space-y-2 text-sm text-gray-400">
            <p>
              • 자주 묻는 질문:{' '}
              <a href="/faq" className="text-blue-600 hover:underline">
                FAQ 보기
              </a>
            </p>
            <p>
              • 사용 가이드:{' '}
              <a href="/guide" className="text-blue-600 hover:underline">
                가이드 읽기
              </a>
            </p>
            <p>• 문의하기: support@pdf-to-epub.com</p>
          </div>
        </div>
      </div>
    </div>
  )
}

// 에러 경계 컴포넌트
export class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(_error: Error, _errorInfo: React.ErrorInfo) {
    // TODO: 에러 로깅 서비스로 전송
    // console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return <Error error={{ message: this.state.error?.message, code: 'COMPONENT_ERROR' }} />
    }

    return this.props.children
  }
}

export default Error
