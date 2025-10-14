import React from 'react'
import { clsx } from 'clsx'

export const LoadingSpinner = ({ size = 'md', className }) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12',
  }

  return (
    <div
      className={clsx(
        'loading-spinner',
        sizeClasses[size],
        className
      )}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  )
}

export const LoadingDots = ({ className }) => {
  return (
    <div className={clsx('loading-dots', className)}>
      <div></div>
      <div></div>
      <div></div>
    </div>
  )
}

export const LoadingCard = ({ className }) => {
  return (
    <div className={clsx('card animate-pulse', className)}>
      <div className="card-header">
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      </div>
      <div className="card-content space-y-3">
        <div className="h-3 bg-gray-200 rounded"></div>
        <div className="h-3 bg-gray-200 rounded w-5/6"></div>
        <div className="h-3 bg-gray-200 rounded w-4/6"></div>
      </div>
    </div>
  )
}


