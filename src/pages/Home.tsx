import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileUpload, UsageIndicator } from '../components/common/index.ts'
import { useAuth } from '../hooks/useAuth'

const Home: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isPremium, setIsPremium] = useState(false)
  const [dailyUsage, setDailyUsage] = useState(0)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // For now, set default values. In a real app, you'd fetch this from your API
    if (user) {
      setIsPremium(false) // This would come from your user data
      setDailyUsage(2) // This would come from your usage tracking
    }
    setIsLoading(false)
  }, [user])

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    // 파일 선택 후 변환 페이지로 이동
    navigate('/upload', { state: { file } })
  }

  // These functions are now handled by the Header component
  // const handleGoogleLogin = async () => {
  //   navigate('/login')
  // }

  // const handleLogout = async () => {
  //   try {
  //     await signOut()
  //   } catch (error) {
  //     // TODO: Add proper error handling
  //   }
  // }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 메인 콘텐츠 */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* 히어로 섹션 */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">PDF를 EPUB으로 쉽게 변환하세요</h2>
          <p className="text-xl text-gray-600 mb-8">
            OCR과 AI를 활용하여 고품질의 전자책을 만들어보세요
          </p>
        </div>

        {/* 파일 업로드 영역 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 mb-8">
          <FileUpload
            onFileSelect={handleFileSelect}
            maxSize={isPremium ? 300 : 10}
            className="mb-6"
          />

          {selectedFile && (
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                선택된 파일: {selectedFile.name}
              </p>
              <button
                onClick={() => handleFileSelect(selectedFile)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                변환 시작
              </button>
            </div>
          )}
        </div>

        {/* 플랜 비교 및 사용량 표시 */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* 무료 플랜 */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">무료 플랜</h3>
            <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
              <li>• 최대 10MB 파일</li>
              <li>• 기본 텍스트 추출</li>
              <li>• 제한된 이미지 처리</li>
              <li>• DeepSeek Free (일일 5회)</li>
            </ul>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">무료</p>
          </div>

          {/* 프리미엄 플랜 */}
          <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/10 rounded-lg shadow-sm p-6 border-2 border-yellow-200">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              프리미엄 플랜
            </h3>
            <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
              <li>• 최대 300MB 파일</li>
              <li>• 고급 OCR 기능 (한글/영어)</li>
              <li>• 고해상도 이미지 처리</li>
              <li>• 무제한 LLM 사용</li>
              <li>• 광고 제거</li>
            </ul>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              $9.99<span className="text-sm font-normal">/월</span>
            </p>
            <button
              onClick={() => navigate('/premium')}
              className="mt-4 w-full bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg font-medium transition-colors"
            >
              프리미엄 시작하기
            </button>
          </div>
        </div>

        {/* 사용량 표시 (무료 사용자만) */}
        {!isPremium && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-8">
            <UsageIndicator dailyUsage={dailyUsage} dailyLimit={5} isPremium={isPremium} />
          </div>
        )}

        {/* 최근 변환 기록 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            최근 변환 기록
          </h3>
          <div className="text-center text-gray-500 dark:text-gray-400 py-8">
            <p>아직 변환한 파일이 없습니다.</p>
            <p className="text-sm mt-2">PDF 파일을 업로드하여 첫 번째 EPUB를 만들어보세요!</p>
          </div>
        </div>
      </main>
    </div>
  )
}

export default Home
