import React from 'react'
import { Zap, Clock, TrendingUp } from 'lucide-react'

interface UsageIndicatorProps {
  dailyUsage: number
  dailyLimit: number
  isPremium: boolean
}

const UsageIndicator: React.FC<UsageIndicatorProps> = ({ dailyUsage, dailyLimit, isPremium }) => {
  const usagePercentage = (dailyUsage / dailyLimit) * 100
  const remaining = dailyLimit - dailyUsage
  const isNearLimit = usagePercentage >= 80

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Daily Usage</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              {isPremium ? 'Unlimited conversions' : `${remaining} conversions remaining`}
            </p>
          </div>
        </div>

        <div className="text-right">
          <div className="text-2xl font-bold text-slate-900 dark:text-white">
            {dailyUsage}/{dailyLimit}
          </div>
          <div className="text-sm text-slate-600 dark:text-slate-400">
            {usagePercentage.toFixed(0)}% used
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-600 dark:text-slate-400">Usage Progress</span>
          <span
            className={`font-medium ${isNearLimit ? 'text-orange-600 dark:text-orange-400' : 'text-slate-600 dark:text-slate-400'}`}
          >
            {usagePercentage.toFixed(0)}%
          </span>
        </div>

        <div className="relative">
          <div className="w-full h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className={`
                h-full rounded-full transition-all duration-500 ease-out
                ${
                  isNearLimit
                    ? 'bg-gradient-to-r from-orange-400 to-red-500'
                    : 'bg-gradient-to-r from-blue-500 to-purple-600'
                }
              `}
              style={{ width: `${Math.min(usagePercentage, 100)}%` }}
            />
          </div>

          {/* Progress indicators */}
          <div className="absolute -top-1 w-full h-5 flex justify-between">
            {[25, 50, 75, 100].map(percent => (
              <div
                key={percent}
                className={`
                  w-1 h-1 rounded-full transition-all duration-300
                  ${
                    usagePercentage >= percent
                      ? 'bg-white shadow-lg'
                      : 'bg-slate-400 dark:bg-slate-500'
                  }
                `}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Status Messages */}
      {!isPremium && (
        <div className="space-y-3">
          {isNearLimit && (
            <div className="p-4 bg-gradient-to-r from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 border border-orange-200 dark:border-orange-800 rounded-xl">
              <div className="flex items-center space-x-3">
                <TrendingUp className="w-5 h-5 text-orange-500" />
                <div>
                  <p className="text-sm font-medium text-orange-800 dark:text-orange-400">
                    Approaching daily limit!
                  </p>
                  <p className="text-xs text-orange-600 dark:text-orange-500">
                    Consider upgrading to Premium for unlimited conversions
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-200 dark:border-blue-800 rounded-xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Clock className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="text-sm font-medium text-blue-800 dark:text-blue-400">
                    Resets in 24 hours
                  </p>
                  <p className="text-xs text-blue-600 dark:text-blue-500">
                    Your daily limit refreshes automatically
                  </p>
                </div>
              </div>

              <button className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-medium rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-lg shadow-blue-500/25">
                Upgrade
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Premium Benefits */}
      {isPremium && (
        <div className="p-4 bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-medium text-yellow-800 dark:text-yellow-400">
                Premium Active
              </p>
              <p className="text-xs text-yellow-600 dark:text-yellow-500">
                Enjoy unlimited conversions and premium features
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default UsageIndicator
