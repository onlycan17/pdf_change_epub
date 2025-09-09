import React from 'react'
import { AlertTriangle, Crown } from 'lucide-react'

interface UsageIndicatorProps {
  dailyUsage: number
  dailyLimit: number
  isPremium: boolean
  className?: string
}

const UsageIndicator: React.FC<UsageIndicatorProps> = ({
  dailyUsage,
  dailyLimit,
  isPremium,
  className = '',
}) => {
  const usagePercentage = (dailyUsage / dailyLimit) * 100
  const isNearLimit = usagePercentage >= 80
  const isOverLimit = usagePercentage >= 100

  if (isPremium) {
    return (
      <div
        className={`flex items-center space-x-2 px-3 py-2 bg-yellow-50 border border-yellow-200 rounded-lg ${className}`}
      >
        <Crown className="h-4 w-4 text-yellow-600" />
        <span className="text-sm font-medium text-yellow-800">프리미엄 플랜 활성화</span>
        <span className="text-xs text-yellow-600">무제한 LLM 사용</span>
      </div>
    )
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600">오늘 사용량 (DeepSeek Free)</span>
        <span
          className={`font-medium ${isOverLimit ? 'text-red-600' : isNearLimit ? 'text-orange-600' : 'text-gray-900'}`}
        >
          {dailyUsage} / {dailyLimit}회
        </span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${
            isOverLimit ? 'bg-red-600' : isNearLimit ? 'bg-orange-500' : 'bg-blue-600'
          }`}
          style={{ width: `${Math.min(usagePercentage, 100)}%` }}
        ></div>
      </div>

      {isNearLimit && !isOverLimit && (
        <div className="flex items-center space-x-2 text-sm text-orange-600">
          <AlertTriangle className="h-4 w-4" />
          <span>사용량이 얼마 남지 않았습니다</span>
        </div>
      )}

      {isOverLimit && (
        <div className="flex items-center space-x-2 text-sm text-red-600">
          <AlertTriangle className="h-4 w-4" />
          <span>일일 사용량을 초과했습니다. 프리미엄으로 업그레이드하세요.</span>
        </div>
      )}
    </div>
  )
}

export default UsageIndicator
