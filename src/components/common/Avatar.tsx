import React from 'react'

interface AvatarProps {
  email?: string
  size?: number
}

const Avatar: React.FC<AvatarProps> = ({ email, size = 32 }) => {
  const initials = email ? email.charAt(0).toUpperCase() : 'U'
  const dimension = `${size}px`

  return (
    <div
      className="flex items-center justify-center rounded-full bg-blue-600 text-white"
      style={{ width: dimension, height: dimension }}
      aria-label={email ? `${email} 아바타` : '사용자 아바타'}
      title={email}
    >
      <span className="text-sm font-semibold" style={{ lineHeight: 1 }}>
        {initials}
      </span>
    </div>
  )
}

export default Avatar
