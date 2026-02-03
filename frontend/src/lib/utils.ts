import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export const cn = (...inputs: ClassValue[]): string => twMerge(clsx(inputs))

export const formatTokens = (value: number): string => {
  if (!Number.isFinite(value)) {
    return '0'
  }

  const absValue = Math.abs(value)
  if (absValue >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(2)}B`
  }
  if (absValue >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(2)}M`
  }
  if (absValue >= 1_000) {
    return `${(value / 1_000).toFixed(2)}K`
  }

  return value.toFixed(2)
}

export const formatPercentage = (value: number): string => {
  if (!Number.isFinite(value)) {
    return '0%'
  }
  return `${value.toFixed(2)}%`
}
