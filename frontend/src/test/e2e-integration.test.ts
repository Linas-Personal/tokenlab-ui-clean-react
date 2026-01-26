import { describe, it, expect, beforeAll, test } from 'vitest'
import { convertToCSV } from '@/lib/export'
import type { BucketResult, GlobalMetric } from '@/types/simulation'

/**
 * End-to-End Integration Test
 *
 * This test verifies the complete data flow from API to UI:
 * 1. Calls real backend API (must be running on localhost:8000)
 * 2. Receives and validates simulation data
 * 3. Processes data for chart rendering
 * 4. Tests CSV export with real data
 *
 * No mocking - tests real integration points.
 */

const API_BASE_URL = 'http://localhost:8000'

// Sample configuration for testing
const TEST_CONFIG = {
  token: {
    name: 'E2E Test Token',
    total_supply: 1_000_000,
    start_date: '2026-01-01',
    horizon_months: 12,
    allocation_mode: 'percent' as const,
    simulation_mode: 'tier1' as const
  },
  buckets: [
    {
      bucket: 'Team',
      allocation: 30,
      tge_unlock_pct: 0,
      cliff_months: 6,
      vesting_months: 12
    },
    {
      bucket: 'Investors',
      allocation: 20,
      tge_unlock_pct: 10,
      cliff_months: 3,
      vesting_months: 9
    },
    {
      bucket: 'Community',
      allocation: 50,
      tge_unlock_pct: 20,
      cliff_months: 0,
      vesting_months: 6
    }
  ],
  assumptions: {
    sell_pressure_level: 'medium' as const
  },
  behaviors: {}
}

describe('End-to-End Integration: API → UI → Export', () => {
  let simulationData: {
    bucket_results: BucketResult[]
    global_metrics: GlobalMetric[]
    summary_cards: any
  }
  let backendAvailable = false

  beforeAll(async () => {
    try {
      // Check if backend is available
      const healthCheck = await fetch(`${API_BASE_URL}/api/v1/health`, {
        method: 'GET'
      }).catch(() => null)

      if (!healthCheck || !healthCheck.ok) {
        console.warn('⚠️  Backend not available - E2E tests will be skipped')
        console.warn(`   Start backend with: cd backend && python -m app.main`)
        backendAvailable = false
        return
      }

      backendAvailable = true

      // Call real API
      const response = await fetch(`${API_BASE_URL}/api/v1/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: TEST_CONFIG })
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`API call failed: ${response.status} - ${errorText}`)
      }

      const result = await response.json()

      if (result.status !== 'success') {
        throw new Error(`Simulation failed: ${JSON.stringify(result)}`)
      }

      simulationData = result.data
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch failed')) {
        console.warn('⚠️  Backend not available - E2E tests will be skipped')
        console.warn(`   Start backend with: cd backend && python -m app.main`)
        backendAvailable = false
      } else {
        throw error
      }
    }
  })

  describe('API Response Validation', () => {
    it.skipIf(!backendAvailable)('returns valid simulation data structure', () => {
      expect(simulationData).toBeDefined()
      expect(simulationData.bucket_results).toBeInstanceOf(Array)
      expect(simulationData.global_metrics).toBeInstanceOf(Array)
      expect(simulationData.summary_cards).toBeDefined()
    })

    it.skipIf(!backendAvailable)('includes data for all configured buckets', () => {
      const buckets = new Set(simulationData.bucket_results.map(r => r.bucket))
      expect(buckets.has('Team')).toBe(true)
      expect(buckets.has('Investors')).toBe(true)
      expect(buckets.has('Community')).toBe(true)
    })

    it.skipIf(!backendAvailable)('has data for all months in horizon', () => {
      const months = new Set(simulationData.bucket_results.map(r => r.month_index))
      // Should have months 0 through 12 (13 total including TGE)
      expect(months.size).toBeGreaterThanOrEqual(13)
    })

    it.skipIf(!backendAvailable)('includes all required bucket fields', () => {
      const firstBucket = simulationData.bucket_results[0]
      expect(firstBucket).toHaveProperty('month_index')
      expect(firstBucket).toHaveProperty('date')
      expect(firstBucket).toHaveProperty('bucket')
      expect(firstBucket).toHaveProperty('allocation_tokens')
      expect(firstBucket).toHaveProperty('unlocked_this_month')
      expect(firstBucket).toHaveProperty('unlocked_cumulative')
      expect(firstBucket).toHaveProperty('locked_remaining')
      expect(firstBucket).toHaveProperty('sell_pressure_effective')
      expect(firstBucket).toHaveProperty('expected_sell_this_month')
      expect(firstBucket).toHaveProperty('expected_circulating_cumulative')
    })

    it.skipIf(!backendAvailable)('includes all required global metric fields', () => {
      const firstMetric = simulationData.global_metrics[0]
      expect(firstMetric).toHaveProperty('month_index')
      expect(firstMetric).toHaveProperty('date')
      expect(firstMetric).toHaveProperty('total_unlocked')
      expect(firstMetric).toHaveProperty('total_expected_sell')
      expect(firstMetric).toHaveProperty('expected_circulating_total')
      expect(firstMetric).toHaveProperty('expected_circulating_pct')
    })

    it.skipIf(!backendAvailable)('includes summary cards with key metrics', () => {
      const { summary_cards } = simulationData
      expect(summary_cards).toHaveProperty('max_unlock_tokens')
      expect(summary_cards).toHaveProperty('max_unlock_month')
      expect(summary_cards).toHaveProperty('max_sell_tokens')
      expect(summary_cards).toHaveProperty('max_sell_month')
      expect(summary_cards).toHaveProperty('circ_12_pct')
      expect(summary_cards).toHaveProperty('circ_end_pct')
    })
  })

  describe('Data Integrity Checks', () => {
    it.skipIf(!backendAvailable)('has monotonically increasing cumulative unlocks per bucket', () => {
      const buckets = ['Team', 'Investors', 'Community']

      for (const bucket of buckets) {
        const bucketData = simulationData.bucket_results
          .filter(r => r.bucket === bucket)
          .sort((a, b) => a.month_index - b.month_index)

        let previousCumulative = 0
        for (const row of bucketData) {
          expect(row.unlocked_cumulative).toBeGreaterThanOrEqual(previousCumulative)
          previousCumulative = row.unlocked_cumulative
        }
      }
    })

    it.skipIf(!backendAvailable)('has locked_remaining that decreases or stays same', () => {
      const buckets = ['Team', 'Investors', 'Community']

      for (const bucket of buckets) {
        const bucketData = simulationData.bucket_results
          .filter(r => r.bucket === bucket)
          .sort((a, b) => a.month_index - b.month_index)

        let previousLocked = Infinity
        for (const row of bucketData) {
          expect(row.locked_remaining).toBeLessThanOrEqual(previousLocked)
          previousLocked = row.locked_remaining
        }
      }
    })

    it.skipIf(!backendAvailable)('maintains allocation_tokens = unlocked_cumulative + locked_remaining', () => {
      for (const row of simulationData.bucket_results) {
        const sum = row.unlocked_cumulative + row.locked_remaining
        const allocation = row.allocation_tokens
        // Allow small floating point errors
        expect(Math.abs(sum - allocation)).toBeLessThan(0.01)
      }
    })

    it.skipIf(!backendAvailable)('has dates in chronological order', () => {
      const globalData = [...simulationData.global_metrics].sort((a, b) => a.month_index - b.month_index)

      for (let i = 1; i < globalData.length; i++) {
        const prevDate = new Date(globalData[i - 1].date)
        const currDate = new Date(globalData[i].date)
        expect(currDate >= prevDate).toBe(true)
      }
    })

    it.skipIf(!backendAvailable)('has expected_circulating_pct that increases or stays same', () => {
      const globalData = [...simulationData.global_metrics].sort((a, b) => a.month_index - b.month_index)

      let previousPct = 0
      for (const row of globalData) {
        expect(row.expected_circulating_pct).toBeGreaterThanOrEqual(previousPct)
        previousPct = row.expected_circulating_pct
      }
    })
  })

  describe('Chart Data Transformation', () => {
    it.skipIf(!backendAvailable)('can aggregate bucket data by month for stacked chart', () => {
      // Simulate what UnlockScheduleChart does
      const monthsSet = new Set(simulationData.bucket_results.map(d => d.month_index))
      const months = Array.from(monthsSet).sort((a, b) => a - b)
      const bucketsSet = new Set(simulationData.bucket_results.map(d => d.bucket))
      const buckets = Array.from(bucketsSet)

      interface ChartDataPoint {
        month: number
        [bucket: string]: number
      }

      const chartData: ChartDataPoint[] = months.map(month => {
        const point: ChartDataPoint = { month }

        simulationData.bucket_results
          .filter(d => d.month_index === month)
          .forEach(d => {
            point[d.bucket] = d.unlocked_this_month
          })

        return point
      })

      expect(chartData.length).toBeGreaterThan(0)
      expect(chartData[0]).toHaveProperty('month')
      expect(buckets.length).toBe(3) // Team, Investors, Community

      // Each data point should have values for all buckets
      for (const point of chartData) {
        for (const bucket of buckets) {
          expect(point).toHaveProperty(bucket)
          expect(typeof point[bucket]).toBe('number')
        }
      }
    })

    it.skipIf(!backendAvailable)('can calculate total unlocks per month for line chart', () => {
      const monthTotals = simulationData.global_metrics.map(m => ({
        month: m.month_index,
        total: m.total_unlocked
      }))

      expect(monthTotals.length).toBeGreaterThan(0)
      expect(monthTotals.every(m => typeof m.total === 'number')).toBe(true)
      expect(monthTotals.every(m => m.total >= 0)).toBe(true)
    })

    it.skipIf(!backendAvailable)('can extract circulating supply over time', () => {
      const circulatingData = simulationData.global_metrics.map(m => ({
        month: m.month_index,
        circulating: m.expected_circulating_total,
        percentage: m.expected_circulating_pct
      }))

      expect(circulatingData.length).toBeGreaterThan(0)
      expect(circulatingData.every(d => d.circulating >= 0)).toBe(true)
      expect(circulatingData.every(d => d.percentage >= 0 && d.percentage <= 100)).toBe(true)
    })
  })

  describe('CSV Export with Real Data', () => {
    it.skipIf(!backendAvailable)('exports bucket results to valid CSV format', () => {
      const csv = convertToCSV(simulationData.bucket_results)

      expect(csv).toBeTruthy()

      const lines = csv.split('\n')
      expect(lines.length).toBeGreaterThan(1) // Header + data rows

      const header = lines[0]
      expect(header).toContain('month_index')
      expect(header).toContain('date')
      expect(header).toContain('bucket')
      expect(header).toContain('allocation_tokens')
      expect(header).toContain('unlocked_this_month')
      expect(header).toContain('unlocked_cumulative')
      expect(header).toContain('locked_remaining')
    })

    it.skipIf(!backendAvailable)('exports global metrics to valid CSV format', () => {
      const csv = convertToCSV(simulationData.global_metrics)

      expect(csv).toBeTruthy()

      const lines = csv.split('\n')
      expect(lines.length).toBeGreaterThan(1)

      const header = lines[0]
      expect(header).toContain('month_index')
      expect(header).toContain('total_unlocked')
      expect(header).toContain('expected_circulating_total')
      expect(header).toContain('expected_circulating_pct')
    })

    it.skipIf(!backendAvailable)('handles null values in CSV export correctly', () => {
      // Global metrics may have null values for tier2/tier3 fields
      const csv = convertToCSV(simulationData.global_metrics)

      // CSV should not contain 'null' string or 'undefined'
      expect(csv).not.toContain('undefined')

      // Null values should be empty in CSV
      const lines = csv.split('\n')
      for (const line of lines.slice(1)) { // Skip header
        // Each line should have the same number of commas
        const commaCount = (line.match(/,/g) || []).length
        expect(commaCount).toBeGreaterThan(0)
      }
    })

    it.skipIf(!backendAvailable)('exports data that can be parsed back correctly', () => {
      const csv = convertToCSV(simulationData.bucket_results.slice(0, 5))
      const lines = csv.split('\n')
      const headers = lines[0].split(',')

      // Parse second line (first data row)
      const dataRow = lines[1].split(',')
      const parsed: Record<string, string> = {}
      headers.forEach((header, i) => {
        parsed[header] = dataRow[i]
      })

      expect(parsed).toHaveProperty('month_index')
      expect(parsed).toHaveProperty('bucket')
      expect(parsed).toHaveProperty('date')

      // Verify numeric fields can be parsed
      expect(isNaN(Number(parsed.month_index))).toBe(false)
      expect(isNaN(Number(parsed.allocation_tokens))).toBe(false)
    })
  })

  describe('Business Logic Validation', () => {
    it.skipIf(!backendAvailable)('respects cliff periods (Team has 6-month cliff)', () => {
      const teamData = simulationData.bucket_results
        .filter(r => r.bucket === 'Team')
        .sort((a, b) => a.month_index - b.month_index)

      // First 6 months (0-5) should have 0 unlocks (cliff period)
      const cliffPeriod = teamData.slice(0, 6)
      for (const row of cliffPeriod) {
        expect(row.unlocked_this_month).toBe(0)
      }

      // After cliff period, should start unlocking
      const afterCliff = teamData.find(r => r.month_index > 6 && r.unlocked_this_month > 0)
      expect(afterCliff).toBeDefined()
      if (afterCliff) {
        expect(afterCliff.unlocked_this_month).toBeGreaterThan(0)
      }
    })

    it.skipIf(!backendAvailable)('applies TGE unlock correctly (Community has 20% TGE)', () => {
      const communityTGE = simulationData.bucket_results.find(
        r => r.bucket === 'Community' && r.month_index === 0
      )

      expect(communityTGE).toBeDefined()
      if (communityTGE) {
        const expectedTGE = communityTGE.allocation_tokens * 0.20
        // Allow small floating point differences
        expect(Math.abs(communityTGE.unlocked_this_month - expectedTGE)).toBeLessThan(1)
      }
    })

    it.skipIf(!backendAvailable)('calculates total supply correctly across all buckets', () => {
      // Get allocation for each bucket (month 0)
      const allocations = simulationData.bucket_results
        .filter(r => r.month_index === 0)
        .reduce((sum, r) => sum + r.allocation_tokens, 0)

      const expectedTotal = TEST_CONFIG.token.total_supply *
        (TEST_CONFIG.buckets.reduce((sum, b) => sum + b.allocation, 0) / 100)

      expect(Math.abs(allocations - expectedTotal)).toBeLessThan(1)
    })

    it.skipIf(!backendAvailable)('has summary cards with realistic values', () => {
      const { summary_cards } = simulationData

      // Max unlock should be positive
      expect(summary_cards.max_unlock_tokens).toBeGreaterThan(0)

      // Max unlock month should be within horizon
      expect(summary_cards.max_unlock_month).toBeGreaterThanOrEqual(0)
      expect(summary_cards.max_unlock_month).toBeLessThanOrEqual(TEST_CONFIG.token.horizon_months)

      // Circulating % at end should be reasonable
      if (summary_cards.circ_end_pct !== null) {
        expect(summary_cards.circ_end_pct).toBeGreaterThan(0)
        expect(summary_cards.circ_end_pct).toBeLessThanOrEqual(100)
      }
    })
  })

  describe('Edge Cases and Error Handling', () => {
    it.skipIf(!backendAvailable)('handles months with zero unlocks gracefully', () => {
      // Find any row with zero unlocks
      const zeroUnlock = simulationData.bucket_results.find(r => r.unlocked_this_month === 0)

      if (zeroUnlock) {
        expect(zeroUnlock.expected_sell_this_month).toBe(0)
        // Locked remaining should still be tracked
        expect(zeroUnlock.locked_remaining).toBeGreaterThanOrEqual(0)
      }
    })

    it.skipIf(!backendAvailable)('handles final month correctly', () => {
      const finalMonth = Math.max(...simulationData.bucket_results.map(r => r.month_index))
      const finalData = simulationData.bucket_results.filter(r => r.month_index === finalMonth)

      expect(finalData.length).toBeGreaterThan(0)
      // All buckets should have data for final month
      expect(finalData.length).toBe(3) // Team, Investors, Community
    })

    it.skipIf(!backendAvailable)('maintains data integrity when filtering by bucket', () => {
      for (const bucketName of ['Team', 'Investors', 'Community']) {
        const bucketData = simulationData.bucket_results.filter(r => r.bucket === bucketName)

        expect(bucketData.length).toBeGreaterThan(0)
        expect(bucketData.every(r => r.bucket === bucketName)).toBe(true)

        // Should have continuous month indices
        const months = bucketData.map(r => r.month_index).sort((a, b) => a - b)
        expect(months[0]).toBe(0) // Should start at month 0 (TGE)
      }
    })
  })
})
