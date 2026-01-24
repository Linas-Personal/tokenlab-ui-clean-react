import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { UnlockScheduleChart } from './UnlockScheduleChart'
import type { BucketResult } from '@/types/simulation'

describe('UnlockScheduleChart', () => {
  const mockData: BucketResult[] = [
    {
      month_index: 0,
      date: '2026-01-01',
      bucket: 'Team',
      allocation_tokens: 300000,
      unlocked_this_month: 0,
      unlocked_cumulative: 0,
      locked_remaining: 300000,
      sell_pressure_effective: 0.25,
      expected_sell_this_month: 0,
      expected_circulating_cumulative: 0
    },
    {
      month_index: 1,
      date: '2026-02-01',
      bucket: 'Team',
      allocation_tokens: 300000,
      unlocked_this_month: 10000,
      unlocked_cumulative: 10000,
      locked_remaining: 290000,
      sell_pressure_effective: 0.25,
      expected_sell_this_month: 2500,
      expected_circulating_cumulative: 7500
    },
    {
      month_index: 0,
      date: '2026-01-01',
      bucket: 'Investors',
      allocation_tokens: 200000,
      unlocked_this_month: 20000,
      unlocked_cumulative: 20000,
      locked_remaining: 180000,
      sell_pressure_effective: 0.25,
      expected_sell_this_month: 5000,
      expected_circulating_cumulative: 15000
    }
  ]

  it('renders without crashing with valid data', () => {
    render(<UnlockScheduleChart data={mockData} />)
    expect(screen.getByText('Monthly Unlock Schedule by Bucket')).toBeInTheDocument()
  })

  it('displays chart description', () => {
    render(<UnlockScheduleChart data={mockData} />)
    expect(screen.getByText(/Tokens unlocking each month across all vesting buckets/)).toBeInTheDocument()
  })

  it('renders empty state when no data provided', () => {
    render(<UnlockScheduleChart data={[]} />)
    expect(screen.getByText('Monthly Unlock Schedule by Bucket')).toBeInTheDocument()
  })

  it('renders with single bucket', () => {
    const singleBucket = mockData.filter(d => d.bucket === 'Team')
    render(<UnlockScheduleChart data={singleBucket} />)
    expect(screen.getByText('Monthly Unlock Schedule by Bucket')).toBeInTheDocument()
  })
})
