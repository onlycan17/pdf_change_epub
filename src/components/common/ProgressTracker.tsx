import React from 'react'
import { CheckCircle, Clock, AlertCircle, Loader } from 'lucide-react'

interface ProgressStep {
  id: string
  label: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  description?: string
}

interface ProgressTrackerProps {
  steps: ProgressStep[]
  currentStep?: string
  className?: string
}

const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  steps,
  currentStep,
  className = '',
}) => {
  const getStepIcon = (status: ProgressStep['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'processing':
        return <Loader className="h-5 w-5 text-blue-600 animate-spin" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-600" />
      default:
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }

  const getStepColor = (status: ProgressStep['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-600'
      case 'processing':
        return 'text-blue-600'
      case 'error':
        return 'text-red-600'
      default:
        return 'text-gray-400'
    }
  }

  const getConnectorColor = (index: number) => {
    const currentStepIndex = steps.findIndex(step => step.id === currentStep)
    if (index < currentStepIndex) {
      return 'bg-green-600'
    } else if (index === currentStepIndex && steps[index]?.status === 'processing') {
      return 'bg-blue-600'
    } else if (steps[index]?.status === 'error') {
      return 'bg-red-600'
    }
    return 'bg-gray-300'
  }

  return (
    <div className={`w-full ${className}`}>
      <div className="space-y-4">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-start space-x-4">
            {/* Step Icon */}
            <div className="flex-shrink-0">
              <div
                className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                  step.status === 'completed'
                    ? 'bg-green-100 border-green-600'
                    : step.status === 'processing'
                      ? 'bg-blue-100 border-blue-600'
                      : step.status === 'error'
                        ? 'bg-red-100 border-red-600'
                        : 'bg-gray-100 border-gray-300'
                }`}
              >
                {getStepIcon(step.status)}
              </div>
            </div>

            {/* Step Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h3 className={`text-sm font-medium ${getStepColor(step.status)}`}>{step.label}</h3>
                {step.status === 'processing' && (
                  <span className="text-xs text-blue-600 font-medium">진행 중...</span>
                )}
              </div>
              {step.description && <p className="text-sm text-gray-600 mt-1">{step.description}</p>}
            </div>

            {/* Connector Line (except for last item) */}
            {index < steps.length - 1 && (
              <div className="flex justify-center w-10">
                <div className={`w-0.5 h-8 ${getConnectorColor(index)}`}></div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Progress Summary */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">전체 진행률</span>
          <span className="font-medium text-gray-900">
            {steps.filter(step => step.status === 'completed').length} / {steps.length}
          </span>
        </div>
        <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{
              width: `${(steps.filter(step => step.status === 'completed').length / steps.length) * 100}%`,
            }}
          ></div>
        </div>
      </div>
    </div>
  )
}

export default ProgressTracker
