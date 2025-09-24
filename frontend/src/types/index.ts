// Common types
export interface User {
  id: string
  email: string
  name: string
  isPremium: boolean
  subscriptionEndDate?: string
}

export interface ConversionJob {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  fileName: string
  fileSize: number
  progress: number
  createdAt: string
  completedAt?: string
  downloadUrl?: string
  errorMessage?: string
}

export interface FileInfo {
  name: string
  size: number
  type: string
  lastModified: number
}

export interface ConversionOptions {
  enableOCR: boolean
  language: string
  imageQuality: 'low' | 'medium' | 'high'
  preserveLayout: boolean
  includeMetadata: boolean
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

export interface AuthResponse {
  user: User
  token: string
}

export interface ConversionResponse {
  jobId: string
  status: string
  estimatedTime?: number
}

// Form types
export interface LoginFormData {
  email: string
  password: string
}

export interface RegisterFormData {
  name: string
  email: string
  password: string
  confirmPassword: string
}

// Notification types
export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  duration?: number
}

// Component props types
export interface ButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  onClick?: () => void
  type?: 'button' | 'submit' | 'reset'
  className?: string
}

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
}