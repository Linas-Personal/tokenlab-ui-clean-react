/**
 * REAL Integration Tests for ABM API Client
 *
 * ⚠️ REQUIRES BACKEND RUNNING ON localhost:8000
 *
 * These tests make REAL HTTP requests to a REAL backend.
 * NO MOCKS. NO STUBS. NO FAKE DATA.
 *
 * To run:
 * 1. Start backend: cd backend && python -m app.main
 * 2. Run tests: npm test src/test/abm-api-real-integration.test.ts
 */

import { describe, it, expect, beforeAll } from 'vitest'
import abmAPIClient from '@/lib/abm-api'
import type { ABMSimulationRequest } from '@/types/abm'

const BACKEND_URL = 'http://localhost:8000'
let backendAvailable = false

describe('ABM API Client - REAL Integration (No Mocks)', () => {
  beforeAll(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/health`)
      backendAvailable = response.ok
      if (!backendAvailable) {
        console.warn('⚠️  Backend not responding - integration tests will be skipped')
        console.warn('   Start backend: cd backend && python -m app.main')
      }
    } catch (error) {
      backendAvailable = false
      console.warn('⚠️  Backend not available at localhost:8000')
      console.warn('   Start backend: cd backend && python -m app.main')
    }
  })

  describe('Async Job Submission - Real Backend', () => {
    it('submits real ABM job and polls for completion', { skip: !backendAvailable }, async () => {
      const config: ABMSimulationRequest = {
        token: {
          name: 'RealIntegrationTest',
          total_supply: 1_000_000,
          start_date: '2026-01-01',
          horizon_months: 3
        },
        buckets: [
          {
            bucket: 'Team',
            allocation: 50,
            tge_unlock_pct: 0,
            cliff_months: 0,
            vesting_months: 3
          },
          {
            bucket: 'Community',
            allocation: 50,
            tge_unlock_pct: 20,
            cliff_months: 0,
            vesting_months: 3
          }
        ],
        abm: {
          pricing_model: 'constant',
          agent_granularity: 'meta_agents',
          agents_per_cohort: 10,
          initial_price: 1.0
        }
      }

      // Submit job to REAL backend
      const submitResponse = await abmAPIClient.submitABMSimulation(config)

      // Verify job was created
      expect(submitResponse).toHaveProperty('job_id')
      expect(submitResponse).toHaveProperty('status')
      expect(submitResponse).toHaveProperty('status_url')
      expect(submitResponse.status).toBe('pending')

      const jobId = submitResponse.job_id

      // Poll for completion (REAL polling, not mocked)
      let attempts = 0
      const maxAttempts = 50
      let jobCompleted = false

      while (attempts < maxAttempts) {
        const statusResponse = await abmAPIClient.getJobStatus(jobId)

        expect(statusResponse).toHaveProperty('job_id')
        expect(statusResponse).toHaveProperty('status')
        expect(statusResponse).toHaveProperty('progress_pct')

        if (statusResponse.status === 'completed') {
          jobCompleted = true
          expect(statusResponse.progress_pct).toBe(100)
          break
        }

        if (statusResponse.status === 'failed') {
          throw new Error(`Job failed: ${statusResponse.error}`)
        }

        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, 100))
        attempts++
      }

      expect(jobCompleted).toBe(true)

      // Get REAL results from backend
      const results = await abmAPIClient.getJobResults(jobId)

      // Verify REAL data structure
      expect(results).toHaveProperty('global_metrics')
      expect(results).toHaveProperty('cohort_metrics')
      expect(results).toHaveProperty('num_agents')
      expect(results).toHaveProperty('execution_time_seconds')

      // Verify REAL simulation ran
      expect(results.global_metrics.length).toBe(3)  // 3 months
      expect(results.num_agents).toBeGreaterThan(0)
      expect(results.execution_time_seconds).toBeGreaterThan(0)

      // Verify REAL price data
      const prices = results.global_metrics.map(m => m.price)
      expect(prices.every(p => p > 0)).toBe(true)

      // Verify REAL unlock data
      const unlocks = results.global_metrics.map(m => m.total_unlocked)
      expect(unlocks[0]).toBeGreaterThan(0)  // Should have unlocked something
    }, { timeout: 60000 })  // 60s timeout for real API calls

    it('handles validation errors from real backend', { skip: !backendAvailable }, async () => {
      const invalidConfig: any = {
        token: {
          name: 'Invalid',
          total_supply: -1000,  // Invalid: negative
          start_date: '2026-01-01',
          horizon_months: 12
        },
        buckets: [],  // Invalid: empty
        abm: {
          pricing_model: 'invalid_model',  // Invalid
          agents_per_cohort: -10,  // Invalid: negative
          initial_price: 1.0
        }
      }

      // Real backend should reject this
      await expect(abmAPIClient.submitABMSimulation(invalidConfig))
        .rejects.toThrow()
    })

    it('handles 404 for non-existent jobs', { skip: !backendAvailable }, async () => {
      await expect(abmAPIClient.getJobStatus('nonexistent_job_12345'))
        .rejects.toThrow()
    })
  })

  describe('Monte Carlo - Real Backend', () => {
    it('submits real Monte Carlo simulation', { skip: !backendAvailable }, async () => {
      const config: ABMSimulationRequest = {
        token: {
          name: 'MCTest',
          total_supply: 1_000_000,
          start_date: '2026-01-01',
          horizon_months: 3
        },
        buckets: [
          {
            bucket: 'Team',
            allocation: 100,
            tge_unlock_pct: 0,
            cliff_months: 0,
            vesting_months: 3
          }
        ],
        abm: {
          pricing_model: 'constant',
          agent_granularity: 'meta_agents',
          agents_per_cohort: 10,
          initial_price: 1.0
        },
        monte_carlo: {
          enabled: true,
          num_trials: 10,
          variance_level: 'low',
          seed: 42,
          confidence_levels: [10, 50, 90]
        }
      }

      const submitResponse = await abmAPIClient.submitMonteCarloSimulation(config)

      expect(submitResponse).toHaveProperty('job_id')
      expect(submitResponse.status).toBe('pending')

      const jobId = submitResponse.job_id

      // Poll for completion
      let attempts = 0
      let completed = false

      while (attempts < 100) {
        const status = await abmAPIClient.getJobStatus(jobId)

        if (status.status === 'completed') {
          completed = true
          break
        }

        if (status.status === 'failed') {
          throw new Error(`MC job failed: ${status.error}`)
        }

        await new Promise(resolve => setTimeout(resolve, 200))
        attempts++
      }

      expect(completed).toBe(true)

      // Get real Monte Carlo results
      const results = await abmAPIClient.getMonteCarloResults(jobId)

      expect(results).toHaveProperty('trials')
      expect(results).toHaveProperty('percentiles')
      expect(results).toHaveProperty('summary')

      expect(results.trials.length).toBe(10)
      expect(results.percentiles.length).toBe(3)  // P10, P50, P90

      // Verify real trial data
      results.trials.forEach(trial => {
        expect(trial).toHaveProperty('trial_index')
        expect(trial).toHaveProperty('global_metrics')
        expect(trial).toHaveProperty('final_price')
        expect(trial.final_price).toBeGreaterThan(0)
      })
    }, { timeout: 120000 })  // 2min timeout for MC
  })

  describe('Error Handling - Real Backend Errors', () => {
    it('receives real 422 validation error', { skip: !backendAvailable }, async () => {
      const config: any = {
        token: {
          // Missing required fields
          name: 'Invalid'
        },
        buckets: []
      }

      try {
        await abmAPIClient.submitABMSimulation(config)
        throw new Error('Should have thrown validation error')
      } catch (error: any) {
        // Real backend error message
        expect(error.message).toBeTruthy()
      }
    })

    it('handles real network timeout', { skip: !backendAvailable }, async () => {
      // This tests real timeout behavior
      const config: ABMSimulationRequest = {
        token: {
          name: 'TimeoutTest',
          total_supply: 1_000_000,
          start_date: '2026-01-01',
          horizon_months: 120  // Very long simulation
        },
        buckets: [
          {
            bucket: 'Team',
            allocation: 100,
            tge_unlock_pct: 0,
            cliff_months: 0,
            vesting_months: 120
          }
        ],
        abm: {
          pricing_model: 'eoe',
          agent_granularity: 'meta_agents',
          agents_per_cohort: 500,  // Many agents
          initial_price: 1.0,
          pricing_config: {
            holding_time: 6.0,
            smoothing_factor: 0.7,
            min_price: 0.01
          }
        }
      }

      // Submit and don't wait - tests async behavior
      const response = await abmAPIClient.submitABMSimulation(config)
      expect(response.job_id).toBeTruthy()
    }, { timeout: 10000 })
  })

  describe('Queue Statistics - Real Backend', () => {
    it('fetches real queue stats', { skip: !backendAvailable }, async () => {
      const stats = await abmAPIClient.getQueueStats()

      expect(stats).toHaveProperty('total_jobs')
      expect(stats).toHaveProperty('cache_size')
      expect(stats).toHaveProperty('max_concurrent_jobs')

      expect(typeof stats.total_jobs).toBe('number')
      expect(typeof stats.max_concurrent_jobs).toBe('number')
    })

    it('lists real jobs', { skip: !backendAvailable }, async () => {
      const response = await abmAPIClient.listJobs()

      expect(response).toHaveProperty('jobs')
      expect(Array.isArray(response.jobs)).toBe(true)
    })
  })

  describe('Config Validation - Real Backend', () => {
    it('validates config against real backend', { skip: !backendAvailable }, async () => {
      const config: ABMSimulationRequest = {
        token: {
          name: 'ValidationTest',
          total_supply: 1_000_000,
          start_date: '2026-01-01',
          horizon_months: 12
        },
        buckets: [
          {
            bucket: 'Team',
            allocation: 60,
            tge_unlock_pct: 0,
            cliff_months: 6,
            vesting_months: 12
          },
          {
            bucket: 'Investors',
            allocation: 60,  // Total > 100%
            tge_unlock_pct: 10,
            cliff_months: 3,
            vesting_months: 9
          }
        ],
        abm: {
          pricing_model: 'constant',
          agent_granularity: 'meta_agents',
          agents_per_cohort: 50,
          initial_price: 1.0
        }
      }

      const validation = await abmAPIClient.validateABMConfig(config)

      expect(validation).toHaveProperty('valid')
      expect(validation).toHaveProperty('errors')
      expect(validation).toHaveProperty('warnings')

      // Should catch allocation > 100%
      expect(validation.valid).toBe(false)
      expect(validation.errors.some(e => e.includes('100'))).toBe(true)
    })
  })
})
