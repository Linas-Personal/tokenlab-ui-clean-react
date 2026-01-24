import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '@/App'

/**
 * Config Import/Upload Functionality Tests
 *
 * Tests the JSON config file import feature in the UI.
 * Validates file upload handling, JSON parsing, form state updates,
 * and error handling for invalid configs.
 */

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false }
  }
})

function AppWrapper() {
  return (
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  )
}

describe('Config Import/Upload Functionality', () => {
  describe('Import Button Rendering', () => {
    it('renders import config button', () => {
      render(<AppWrapper />)
      const importButton = screen.getByText(/Import Config/i)
      expect(importButton).toBeInTheDocument()
    })

    it('has upload icon in button', () => {
      render(<AppWrapper />)
      const importButton = screen.getByRole('button', { name: /Import Config/i })
      expect(importButton).toBeInTheDocument()
      // Icon is rendered as SVG
      const svg = importButton.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('has hidden file input that accepts JSON', () => {
      const { container } = render(<AppWrapper />)
      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement
      expect(fileInput).toBeInTheDocument()
      expect(fileInput.accept).toBe('.json')
      expect(fileInput.className).toContain('hidden')
    })
  })

  describe('File Upload Interaction', () => {
    it('triggers file input when import button clicked', async () => {
      const user = userEvent.setup()
      const { container } = render(<AppWrapper />)

      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement
      const clickSpy = vi.spyOn(fileInput, 'click')

      const importButton = screen.getByRole('button', { name: /Import Config/i })
      await user.click(importButton)

      expect(clickSpy).toHaveBeenCalled()
    })
  })

  describe('Valid Config Import', () => {
    it('loads valid config JSON into form', async () => {
      const user = userEvent.setup()
      const { container } = render(<AppWrapper />)

      const validConfig = {
        token: {
          name: 'Imported Token',
          total_supply: 5000000,
          start_date: '2026-06-01',
          horizon_months: 18,
          allocation_mode: 'percent',
          simulation_mode: 'tier1'
        },
        buckets: [
          {
            bucket: 'Imported Bucket',
            allocation: 50,
            tge_unlock_pct: 5,
            cliff_months: 3,
            vesting_months: 12,
            unlock_type: 'linear'
          }
        ],
        assumptions: {
          sell_pressure_level: 'high'
        },
        behaviors: {}
      }

      const configJSON = JSON.stringify(validConfig)
      const blob = new Blob([configJSON], { type: 'application/json' })
      const file = new File([blob], 'test-config.json', { type: 'application/json' })

      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement

      await user.upload(fileInput, file)

      // Wait for file to be processed and form to update
      await waitFor(() => {
        const nameInput = screen.getByLabelText(/Token Name/i) as HTMLInputElement
        expect(nameInput.value).toBe('Imported Token')
      })

      // Verify other fields were updated
      const supplyInput = screen.getByLabelText(/Total Supply/i) as HTMLInputElement
      expect(supplyInput.value).toBe('5000000')

      const startDateInput = screen.getByLabelText(/Start Date/i) as HTMLInputElement
      expect(startDateInput.value).toBe('2026-06-01')

      const horizonInput = screen.getByLabelText(/Simulation Horizon/i) as HTMLInputElement
      expect(horizonInput.value).toBe('18')
    })

    it('switches to token setup tab after import', async () => {
      const user = userEvent.setup()
      const { container } = render(<AppWrapper />)

      // First navigate away from token setup tab
      const vestingTab = screen.getByRole('tab', { name: /Vesting Schedule/i })
      await user.click(vestingTab)

      const validConfig = {
        token: {
          name: 'Test',
          total_supply: 1000000,
          start_date: '2026-01-01',
          horizon_months: 12,
          allocation_mode: 'percent',
          simulation_mode: 'tier1'
        },
        buckets: [],
        assumptions: { sell_pressure_level: 'medium' },
        behaviors: {}
      }

      const file = new File([JSON.stringify(validConfig)], 'config.json', { type: 'application/json' })
      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement

      await user.upload(fileInput, file)

      // Should switch back to token setup tab
      await waitFor(() => {
        const tokenSetupTab = screen.getByRole('tab', { name: /Token Setup/i })
        expect(tokenSetupTab).toHaveAttribute('data-state', 'active')
      })
    })
  })

  describe('Error Handling', () => {
    it('handles invalid JSON gracefully', async () => {
      const user = userEvent.setup()
      const { container } = render(<AppWrapper />)

      // Create file with invalid JSON
      const invalidJSON = '{ invalid json here }'
      const file = new File([invalidJSON], 'bad-config.json', { type: 'application/json' })

      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement

      // Mock console.error to suppress error output in tests
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

      // This should not crash the app
      await user.upload(fileInput, file)

      // Give time for error to occur if it will
      await waitFor(() => {
        // App should still be rendered
        expect(screen.getByText(/Token Vesting Simulator/i)).toBeInTheDocument()
      })

      consoleError.mockRestore()
    })

    it('handles empty file', async () => {
      const user = userEvent.setup()
      const { container } = render(<AppWrapper />)

      const emptyFile = new File([''], 'empty.json', { type: 'application/json' })
      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement

      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

      await user.upload(fileInput, emptyFile)

      // App should still be rendered
      await waitFor(() => {
        expect(screen.getByText(/Token Vesting Simulator/i)).toBeInTheDocument()
      })

      consoleError.mockRestore()
    })

    it('handles non-JSON file content', async () => {
      const user = userEvent.setup()
      const { container } = render(<AppWrapper />)

      const textContent = 'This is just plain text, not JSON'
      const file = new File([textContent], 'notjson.json', { type: 'application/json' })

      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement

      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

      await user.upload(fileInput, file)

      // App should still be rendered
      await waitFor(() => {
        expect(screen.getByText(/Token Vesting Simulator/i)).toBeInTheDocument()
      })

      consoleError.mockRestore()
    })
  })

  describe('Config Structure Validation', () => {
    it('imports config with all tier 1 fields', async () => {
      const user = userEvent.setup()
      const { container } = render(<AppWrapper />)

      const tier1Config = {
        token: {
          name: 'Tier1Token',
          total_supply: 10000000,
          start_date: '2026-01-01',
          horizon_months: 24,
          allocation_mode: 'percent',
          simulation_mode: 'tier1'
        },
        buckets: [
          {
            bucket: 'Team',
            allocation: 30,
            tge_unlock_pct: 0,
            cliff_months: 12,
            vesting_months: 36,
            unlock_type: 'linear'
          },
          {
            bucket: 'Investors',
            allocation: 20,
            tge_unlock_pct: 10,
            cliff_months: 6,
            vesting_months: 18,
            unlock_type: 'linear'
          }
        ],
        assumptions: {
          sell_pressure_level: 'medium'
        },
        behaviors: {
          cliff_shock: { enabled: false },
          price_trigger: { enabled: false },
          relock: { enabled: false }
        }
      }

      const file = new File([JSON.stringify(tier1Config)], 'tier1.json', { type: 'application/json' })
      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement

      await user.upload(fileInput, file)

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/Token Name/i) as HTMLInputElement
        expect(nameInput.value).toBe('Tier1Token')
      })

      const supplyInput = screen.getByLabelText(/Total Supply/i) as HTMLInputElement
      expect(supplyInput.value).toBe('10000000')
    })

    it('imports config with tier 2 configuration', async () => {
      const user = userEvent.setup()
      const { container } = render(<AppWrapper />)

      const tier2Config = {
        token: {
          name: 'Tier2Token',
          total_supply: 1000000,
          start_date: '2026-03-01',
          horizon_months: 36,
          allocation_mode: 'percent',
          simulation_mode: 'tier2'
        },
        buckets: [
          {
            bucket: 'Treasury',
            allocation: 100,
            tge_unlock_pct: 0,
            cliff_months: 0,
            vesting_months: 24,
            unlock_type: 'linear'
          }
        ],
        assumptions: {
          sell_pressure_level: 'low'
        },
        behaviors: {},
        tier2: {
          staking: {
            enabled: true,
            apy: 0.12,
            max_capacity_pct: 0.5,
            lockup_months: 6,
            participation_rate: 0.3,
            reward_source: 'treasury'
          },
          pricing: {
            enabled: true,
            pricing_model: 'bonding_curve',
            initial_price: 1.0,
            bonding_curve_param: 2.0
          },
          treasury: {
            enabled: true,
            initial_balance_pct: 0.15,
            hold_pct: 0.5,
            liquidity_pct: 0.3,
            buyback_pct: 0.2
          },
          volume: {
            enabled: true,
            volume_model: 'proportional',
            base_daily_volume: 1000000,
            volume_multiplier: 1.0
          }
        }
      }

      const file = new File([JSON.stringify(tier2Config)], 'tier2.json', { type: 'application/json' })
      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement

      await user.upload(fileInput, file)

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/Token Name/i) as HTMLInputElement
        expect(nameInput.value).toBe('Tier2Token')
      })

      // Verify tier 2 mode is selected
      const tierSelect = screen.getByLabelText(/Simulation Tier/i) as HTMLSelectElement
      expect(tierSelect.value).toBe('tier2')
    })
  })

  describe('Real-World Scenarios', () => {
    it('imports exported config (round-trip)', async () => {
      const user = userEvent.setup()
      const { container } = render(<AppWrapper />)

      // This simulates exporting a config and re-importing it
      const exportedConfig = {
        token: {
          name: 'ExportedToken',
          total_supply: 2500000,
          start_date: '2026-02-15',
          horizon_months: 15,
          allocation_mode: 'percent',
          simulation_mode: 'tier1'
        },
        buckets: [
          {
            bucket: 'Community',
            allocation: 60,
            tge_unlock_pct: 15,
            cliff_months: 0,
            vesting_months: 12,
            unlock_type: 'linear'
          },
          {
            bucket: 'Advisors',
            allocation: 40,
            tge_unlock_pct: 0,
            cliff_months: 6,
            vesting_months: 18,
            unlock_type: 'linear'
          }
        ],
        assumptions: {
          sell_pressure_level: 'medium',
          avg_daily_volume_tokens: 500000
        },
        behaviors: {
          cliff_shock: {
            enabled: true,
            multiplier: 2.5,
            buckets: ['Advisors']
          },
          price_trigger: { enabled: false },
          relock: { enabled: false }
        }
      }

      const file = new File([JSON.stringify(exportedConfig, null, 2)], 'exported.json', {
        type: 'application/json'
      })
      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement

      await user.upload(fileInput, file)

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/Token Name/i) as HTMLInputElement
        expect(nameInput.value).toBe('ExportedToken')
      })

      // All fields should be populated correctly
      const supplyInput = screen.getByLabelText(/Total Supply/i) as HTMLInputElement
      expect(supplyInput.value).toBe('2500000')

      const horizonInput = screen.getByLabelText(/Simulation Horizon/i) as HTMLInputElement
      expect(horizonInput.value).toBe('15')
    })

    it('handles minimal valid config', async () => {
      const user = userEvent.setup()
      const { container } = render(<AppWrapper />)

      // Minimal config with only required fields
      const minimalConfig = {
        token: {
          name: 'Minimal',
          total_supply: 1000000,
          start_date: '2026-01-01',
          horizon_months: 12,
          allocation_mode: 'percent',
          simulation_mode: 'tier1'
        },
        buckets: [
          {
            bucket: 'Simple',
            allocation: 100,
            tge_unlock_pct: 0,
            cliff_months: 0,
            vesting_months: 12,
            unlock_type: 'linear'
          }
        ],
        assumptions: {
          sell_pressure_level: 'medium'
        },
        behaviors: {}
      }

      const file = new File([JSON.stringify(minimalConfig)], 'minimal.json', { type: 'application/json' })
      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement

      await user.upload(fileInput, file)

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/Token Name/i) as HTMLInputElement
        expect(nameInput.value).toBe('Minimal')
      })
    })
  })
})
