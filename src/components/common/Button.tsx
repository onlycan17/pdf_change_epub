import React from 'react'

interface ButtonProps {
  children: React.ReactNode
  onClick?: () => void
  variant?:
    | 'primary'
    | 'secondary'
    | 'accent'
    | 'success'
    | 'error'
    | 'ghost'
    | 'outline'
    | 'premium'
  size?: 'sm' | 'base' | 'lg' | 'xl'
  disabled?: boolean
  isLoading?: boolean
  fullWidth?: boolean
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right'
  className?: string
  type?: 'button' | 'submit' | 'reset'
}

const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'base',
  disabled = false,
  isLoading = false,
  fullWidth = false,
  icon,
  iconPosition = 'left',
  className = '',
  type = 'button',
}) => {
  const baseClasses = `
    inline-flex items-center justify-center gap-2 font-medium
    transition-all duration-200 ease-in-out
    focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
  `

  const variantClasses = {
    primary: `
      bg-gradient-to-r from-blue-500 to-purple-600
      text-white
      border border-transparent
      focus:ring-blue-500
      hover:from-blue-600 hover:to-purple-700
      shadow-lg shadow-blue-500/25
    `,
    secondary: `
      bg-white dark:bg-slate-800
      text-slate-700 dark:text-slate-200
      border border-slate-300 dark:border-slate-600
      focus:ring-slate-500
      hover:bg-slate-50 dark:hover:bg-slate-700
      hover:border-slate-400 dark:hover:border-slate-500
    `,
    accent: `
      bg-gradient-to-r from-yellow-400 to-orange-500
      text-white
      border border-transparent
      focus:ring-yellow-500
      hover:from-yellow-500 hover:to-orange-600
      shadow-lg shadow-yellow-500/25
    `,
    success: `
      bg-gradient-to-r from-green-500 to-emerald-600
      text-white
      border border-transparent
      focus:ring-green-500
      hover:from-green-600 hover:to-emerald-700
      shadow-lg shadow-green-500/25
    `,
    error: `
      bg-gradient-to-r from-red-500 to-pink-600
      text-white
      border border-transparent
      focus:ring-red-500
      hover:from-red-600 hover:to-pink-700
      shadow-lg shadow-red-500/25
    `,
    ghost: `
      bg-transparent
      text-slate-600 dark:text-slate-300
      border border-transparent
      focus:ring-slate-500
      hover:bg-slate-100 dark:hover:bg-slate-700
      hover:text-slate-900 dark:hover:text-white
    `,
    outline: `
      bg-transparent
      text-blue-600 dark:text-blue-400
      border border-blue-600 dark:border-blue-400
      focus:ring-blue-500
      hover:bg-blue-50 dark:hover:bg-blue-900/20
      hover:text-blue-700 dark:hover:text-blue-300
    `,
    premium: `
        bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500
        text-white
        border border-transparent
        focus:ring-yellow-500
        hover:from-yellow-500 hover:via-orange-600 hover:to-red-600
        shadow-lg shadow-yellow-500/25
      `,
  }

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm rounded-lg',
    base: 'px-4 py-2 text-base rounded-xl',
    lg: 'px-6 py-3 text-lg rounded-2xl',
    xl: 'px-8 py-4 text-xl rounded-3xl',
  }

  const widthClasses = fullWidth ? 'w-full' : ''

  const allClasses = `
    ${baseClasses}
    ${variantClasses[variant]}
    ${sizeClasses[size]}
    ${widthClasses}
    ${className}
  `

  const handleClick = () => {
    if (!disabled && !isLoading && onClick) {
      onClick()
    }
  }

  return (
    <button
      type={type}
      className={allClasses}
      onClick={handleClick}
      disabled={disabled || isLoading}
    >
      {isLoading && <div className="loading-spinner w-4 h-4"></div>}

      {!isLoading && icon && iconPosition === 'left' && icon}

      <span className={isLoading ? 'opacity-0' : ''}>{children}</span>

      {!isLoading && icon && iconPosition === 'right' && icon}
    </button>
  )
}

export default Button
