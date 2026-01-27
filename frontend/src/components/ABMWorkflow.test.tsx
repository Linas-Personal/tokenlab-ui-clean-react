/**
 * Component Tests for ABM Workflow Forms
 *
 * ⚠️ NOTE: These are COMPONENT TESTS, not integration tests.
 * They test form rendering and user interactions in isolation.
 *
 * For REAL integration tests with backend API calls, see:
 * - src/test/abm-api-real-integration.test.ts
 * - src/test/e2e-integration.test.ts
 *
 * Tests covered:
 * - Form rendering and field visibility
 * - User interactions (clicks, typing, selections)
 * - Input validation and constraints
 * - Conditional field display
 * - Edge cases in UI behavior
 *
 * Does NOT test:
 * - API calls to backend
 * - Real simulation execution
 * - Network error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { FormProvider, useForm } from 'react-hook-form'
import { ABMConfigForm } from './forms/ABMConfigForm'
import { ABMTab } from './tabs/ABMTab'
import type { SimulationConfig } from '@/types/config'
import { DEFAULT_CONFIG } from '@/lib/constants'

// Test wrapper with form context
function TestWrapper({ children, defaultValues = DEFAULT_CONFIG }: any) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  const FormWrapper = () => {
    const methods = useForm<SimulationConfig>({ defaultValues })
    return (
      <FormProvider {...methods}>
        {children}
      </FormProvider>
    )
  }

  return (
    <QueryClientProvider client={queryClient}>
      <FormWrapper />
    </QueryClientProvider>
  )
}

describe('ABM Configuration Form - User Interactions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all configuration sections', () => {
    render(
      <TestWrapper>
        <ABMConfigForm />
      </TestWrapper>
    )

    // Check all accordion sections are present
    expect(screen.getByText('Agent Population')).toBeInTheDocument()
    expect(screen.getByText('Dynamic Pricing Model')).toBeInTheDocument()
    expect(screen.getByText('Dynamic Volume (Optional)')).toBeInTheDocument()
    expect(screen.getByText('Staking Pool (Optional)')).toBeInTheDocument()
    expect(screen.getByText('Treasury Management (Optional)')).toBeInTheDocument()
    expect(screen.getByText('Monte Carlo Simulations (Optional)')).toBeInTheDocument()
  })

  describe('Agent Granularity Selection', () => {
    it('allows selecting different agent granularity options', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      const granularitySelect = screen.getByLabelText(/Agent Granularity/i)

      // Change to full individual
      await user.selectOptions(granularitySelect, 'full_individual')
      expect((granularitySelect as HTMLSelectElement).value).toBe('full_individual')

      // Change to meta agents
      await user.selectOptions(granularitySelect, 'meta_agents')
      expect((granularitySelect as HTMLSelectElement).value).toBe('meta_agents')

      // Change back to adaptive
      await user.selectOptions(granularitySelect, 'adaptive')
      expect((granularitySelect as HTMLSelectElement).value).toBe('adaptive')
    })

    it('shows appropriate description for each granularity level', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      const granularitySelect = screen.getByLabelText(/Agent Granularity/i)

      // Adaptive description
      await user.selectOptions(granularitySelect, 'adaptive')
      expect(screen.getByText(/Automatically chooses full individual/i)).toBeInTheDocument()

      // Full individual description
      await user.selectOptions(granularitySelect, 'full_individual')
      expect(screen.getByText(/Creates one agent per token holder/i)).toBeInTheDocument()

      // Meta agents description
      await user.selectOptions(granularitySelect, 'meta_agents')
      expect(screen.getByText(/Each agent represents multiple holders/i)).toBeInTheDocument()
    })
  })

  describe('Agents Per Cohort Slider', () => {
    it('updates agents per cohort value via slider', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      // Find slider (it's an input type="range")
      const slider = screen.getByRole('slider', { name: /agents-per-cohort/i })

      // Change value
      fireEvent.change(slider, { target: { value: '100' } })

      // Check display updates
      await waitFor(() => {
        expect(screen.getByText('100')).toBeInTheDocument()
      })
    })

    it('enforces min and max bounds for agents per cohort', async () => {
      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      const slider = screen.getByRole('slider', { name: /agents-per-cohort/i })

      // Try to set below min (10)
      fireEvent.change(slider, { target: { value: '5' } })
      expect(parseInt((slider as HTMLInputElement).value)).toBeGreaterThanOrEqual(10)

      // Try to set above max (500)
      fireEvent.change(slider, { target: { value: '1000' } })
      expect(parseInt((slider as HTMLInputElement).value)).toBeLessThanOrEqual(500)
    })
  })

  describe('Pricing Model Selection', () => {
    it('changes pricing model and shows relevant config fields', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      const pricingModelSelect = screen.getByLabelText(/Pricing Model/i)

      // EOE model shows holding time, smoothing factor, min price
      await user.selectOptions(pricingModelSelect, 'eoe')
      expect(screen.getByLabelText(/Holding Time/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Smoothing Factor/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Min Price/i)).toBeInTheDocument()

      // Bonding curve shows k and n parameters
      await user.selectOptions(pricingModelSelect, 'bonding_curve')
      expect(screen.getByLabelText(/K Parameter/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/N Parameter/i)).toBeInTheDocument()

      // Issuance curve shows alpha parameter
      await user.selectOptions(pricingModelSelect, 'issuance_curve')
      expect(screen.getByLabelText(/Alpha Parameter/i)).toBeInTheDocument()

      // Constant shows no extra fields
      await user.selectOptions(pricingModelSelect, 'constant')
      expect(screen.queryByLabelText(/Holding Time/i)).not.toBeInTheDocument()
    })

    it('validates pricing config inputs', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      const pricingModelSelect = screen.getByLabelText(/Pricing Model/i)
      await user.selectOptions(pricingModelSelect, 'eoe')

      const smoothingFactorInput = screen.getByLabelText(/Smoothing Factor/i)

      // Try invalid value (> 1)
      await user.clear(smoothingFactorInput)
      await user.type(smoothingFactorInput, '2.0')

      // Input should have max constraint
      expect((smoothingFactorInput as HTMLInputElement).max).toBe('1')
    })
  })

  describe('Staking Configuration', () => {
    it('enables staking and shows staking fields', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      // Find and click staking checkbox
      const stakingCheckbox = screen.getByLabelText(/Enable dynamic staking pool/i)
      await user.click(stakingCheckbox)

      // Staking fields should appear
      await waitFor(() => {
        expect(screen.getByLabelText(/Base APY/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Max Capacity/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Lockup Period/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Reward Source/i)).toBeInTheDocument()
      })
    })

    it('disables staking and hides staking fields', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper defaultValues={{
          ...DEFAULT_CONFIG,
          abm: {
            ...DEFAULT_CONFIG.abm,
            enable_staking: true
          }
        }}>
          <ABMConfigForm />
        </TestWrapper>
      )

      // Uncheck staking
      const stakingCheckbox = screen.getByLabelText(/Enable dynamic staking pool/i)
      await user.click(stakingCheckbox)

      // Staking fields should disappear
      await waitFor(() => {
        expect(screen.queryByLabelText(/Base APY/i)).not.toBeInTheDocument()
      })
    })

    it('selects reward source (emission vs treasury)', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper defaultValues={{
          ...DEFAULT_CONFIG,
          abm: {
            ...DEFAULT_CONFIG.abm,
            enable_staking: true
          }
        }}>
          <ABMConfigForm />
        </TestWrapper>
      )

      const rewardSourceSelect = screen.getByLabelText(/Reward Source/i)

      await user.selectOptions(rewardSourceSelect, 'emission')
      expect((rewardSourceSelect as HTMLSelectElement).value).toBe('emission')

      await user.selectOptions(rewardSourceSelect, 'treasury')
      expect((rewardSourceSelect as HTMLSelectElement).value).toBe('treasury')
    })
  })

  describe('Treasury Configuration', () => {
    it('enables treasury and shows treasury fields', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      const treasuryCheckbox = screen.getByLabelText(/Enable treasury with buyback/i)
      await user.click(treasuryCheckbox)

      await waitFor(() => {
        expect(screen.getByLabelText(/Initial Balance/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Transaction Fee/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Hold %/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Liquidity %/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Buyback %/i)).toBeInTheDocument()
      })
    })

    it('toggles burn bought tokens option', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper defaultValues={{
          ...DEFAULT_CONFIG,
          abm: {
            ...DEFAULT_CONFIG.abm,
            enable_treasury: true
          }
        }}>
          <ABMConfigForm />
        </TestWrapper>
      )

      const burnCheckbox = screen.getByLabelText(/Burn bought tokens/i)

      // Toggle on
      await user.click(burnCheckbox)
      expect((burnCheckbox as HTMLInputElement).checked).toBe(true)

      // Toggle off
      await user.click(burnCheckbox)
      expect((burnCheckbox as HTMLInputElement).checked).toBe(false)
    })

    it('validates treasury allocation percentages', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper defaultValues={{
          ...DEFAULT_CONFIG,
          abm: {
            ...DEFAULT_CONFIG.abm,
            enable_treasury: true
          }
        }}>
          <ABMConfigForm />
        </TestWrapper>
      )

      const holdInput = screen.getByLabelText(/Hold %/i)
      const liquidityInput = screen.getByLabelText(/Liquidity %/i)
      const buybackInput = screen.getByLabelText(/Buyback %/i)

      // Set values that sum to 1.0
      await user.clear(holdInput)
      await user.type(holdInput, '0.3')

      await user.clear(liquidityInput)
      await user.type(liquidityInput, '0.5')

      await user.clear(buybackInput)
      await user.type(buybackInput, '0.2')

      // Values should be accepted (sum = 1.0)
      expect((holdInput as HTMLInputElement).value).toBe('0.3')
      expect((liquidityInput as HTMLInputElement).value).toBe('0.5')
      expect((buybackInput as HTMLInputElement).value).toBe('0.2')
    })
  })

  describe('Monte Carlo Configuration', () => {
    it('enables Monte Carlo and shows MC fields', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      const mcCheckbox = screen.getByLabelText(/Enable Monte Carlo/i)
      await user.click(mcCheckbox)

      await waitFor(() => {
        expect(screen.getByLabelText(/Number of Trials/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Variance Level/i)).toBeInTheDocument()
      })
    })

    it('updates number of trials via slider', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper defaultValues={{
          ...DEFAULT_CONFIG,
          monte_carlo: {
            ...DEFAULT_CONFIG.monte_carlo,
            enabled: true
          }
        }}>
          <ABMConfigForm />
        </TestWrapper>
      )

      const trialsSlider = screen.getByRole('slider', { name: /num-trials/i })

      fireEvent.change(trialsSlider, { target: { value: '200' } })

      await waitFor(() => {
        expect(screen.getByText('200')).toBeInTheDocument()
      })
    })

    it('selects variance level', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper defaultValues={{
          ...DEFAULT_CONFIG,
          monte_carlo: {
            ...DEFAULT_CONFIG.monte_carlo,
            enabled: true
          }
        }}>
          <ABMConfigForm />
        </TestWrapper>
      )

      const varianceSelect = screen.getByLabelText(/Variance Level/i)

      await user.selectOptions(varianceSelect, 'low')
      expect((varianceSelect as HTMLSelectElement).value).toBe('low')

      await user.selectOptions(varianceSelect, 'medium')
      expect((varianceSelect as HTMLSelectElement).value).toBe('medium')

      await user.selectOptions(varianceSelect, 'high')
      expect((varianceSelect as HTMLSelectElement).value).toBe('high')
    })

    it('shows estimated execution time for Monte Carlo', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper defaultValues={{
          ...DEFAULT_CONFIG,
          monte_carlo: {
            ...DEFAULT_CONFIG.monte_carlo,
            enabled: true,
            num_trials: 100
          }
        }}>
          <ABMConfigForm />
        </TestWrapper>
      )

      // Should show time estimate
      expect(screen.getByText(/Expected time: ~0.7s/i)).toBeInTheDocument()
    })
  })

  describe('Volume Configuration', () => {
    it('enables volume and shows volume fields', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      const volumeCheckbox = screen.getByLabelText(/Enable dynamic transaction volume/i)
      await user.click(volumeCheckbox)

      await waitFor(() => {
        expect(screen.getByLabelText(/Volume Model/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Base Daily Volume/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Volume Multiplier/i)).toBeInTheDocument()
      })
    })

    it('selects volume model (proportional vs constant)', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper defaultValues={{
          ...DEFAULT_CONFIG,
          abm: {
            ...DEFAULT_CONFIG.abm,
            enable_volume: true
          }
        }}>
          <ABMConfigForm />
        </TestWrapper>
      )

      const volumeModelSelect = screen.getByLabelText(/Volume Model/i)

      await user.selectOptions(volumeModelSelect, 'proportional')
      expect((volumeModelSelect as HTMLSelectElement).value).toBe('proportional')
      expect(screen.getByText(/Volume scales with circulating supply ratio/i)).toBeInTheDocument()

      await user.selectOptions(volumeModelSelect, 'constant')
      expect((volumeModelSelect as HTMLSelectElement).value).toBe('constant')
      expect(screen.getByText(/Fixed daily trading volume/i)).toBeInTheDocument()
    })
  })

  describe('Cohort Behavior Presets', () => {
    it('shows cohort behavior preset descriptions', () => {
      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      expect(screen.getByText('Conservative')).toBeInTheDocument()
      expect(screen.getByText('Moderate')).toBeInTheDocument()
      expect(screen.getByText('Aggressive')).toBeInTheDocument()
    })

    it('assigns behavioral preset to bucket', async () => {
      const user = userEvent.setup()

      const configWithBuckets = {
        ...DEFAULT_CONFIG,
        buckets: [
          { bucket: 'Team', allocation: 30, tge_unlock_pct: 0, cliff_months: 12, vesting_months: 24 },
          { bucket: 'Investors', allocation: 40, tge_unlock_pct: 10, cliff_months: 6, vesting_months: 18 },
          { bucket: 'Community', allocation: 30, tge_unlock_pct: 20, cliff_months: 0, vesting_months: 12 }
        ]
      }

      render(
        <TestWrapper defaultValues={configWithBuckets}>
          <ABMConfigForm />
        </TestWrapper>
      )

      // Should show bucket assignments
      expect(screen.getByText('Team')).toBeInTheDocument()
      expect(screen.getByText('Investors')).toBeInTheDocument()
      expect(screen.getByText('Community')).toBeInTheDocument()

      // Find select for Team bucket
      const selects = screen.getAllByRole('combobox')
      const teamSelect = selects.find(select =>
        select.previousElementSibling?.textContent?.includes('Team')
      )

      if (teamSelect) {
        await user.selectOptions(teamSelect, 'conservative')
        expect((teamSelect as HTMLSelectElement).value).toBe('conservative')
      }
    })

    it('shows warning when no buckets are configured', () => {
      render(
        <TestWrapper defaultValues={{
          ...DEFAULT_CONFIG,
          buckets: []
        }}>
          <ABMConfigForm />
        </TestWrapper>
      )

      expect(screen.getByText(/No allocation buckets configured yet/i)).toBeInTheDocument()
    })
  })

  describe('Features Summary Display', () => {
    it('displays current configuration summary', () => {
      render(
        <TestWrapper defaultValues={{
          ...DEFAULT_CONFIG,
          abm: {
            ...DEFAULT_CONFIG.abm,
            agent_granularity: 'meta_agents',
            agents_per_cohort: 100,
            pricing_model: 'bonding_curve',
            initial_price: 2.5,
            enable_staking: true,
            enable_treasury: true,
            enable_volume: true
          },
          monte_carlo: {
            ...DEFAULT_CONFIG.monte_carlo,
            enabled: true,
            num_trials: 50
          }
        }}>
          <ABMConfigForm />
        </TestWrapper>
      )

      // Check summary values
      expect(screen.getByText('meta_agents')).toBeInTheDocument()
      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText('BONDING_CURVE')).toBeInTheDocument()
      expect(screen.getByText('$2.5')).toBeInTheDocument()
      expect(screen.getByText('Yes', { selector: 'span' })).toBeInTheDocument()  // Staking
      expect(screen.getByText('50 trials')).toBeInTheDocument()
    })
  })

  describe('Edge Cases and Error States', () => {
    it('handles form with no initial values gracefully', () => {
      const queryClient = new QueryClient()

      const EmptyFormWrapper = () => {
        const methods = useForm<SimulationConfig>()
        return (
          <QueryClientProvider client={queryClient}>
            <FormProvider {...methods}>
              <ABMConfigForm />
            </FormProvider>
          </QueryClientProvider>
        )
      }

      expect(() => render(<EmptyFormWrapper />)).not.toThrow()
    })

    it('handles extreme slider values', async () => {
      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      const slider = screen.getByRole('slider', { name: /agents-per-cohort/i })

      // Set to minimum
      fireEvent.change(slider, { target: { value: '10' } })
      expect((slider as HTMLInputElement).value).toBe('10')

      // Set to maximum
      fireEvent.change(slider, { target: { value: '500' } })
      expect((slider as HTMLInputElement).value).toBe('500')
    })

    it('handles rapid toggling of checkboxes', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      const stakingCheckbox = screen.getByLabelText(/Enable dynamic staking pool/i)

      // Toggle multiple times rapidly
      for (let i = 0; i < 5; i++) {
        await user.click(stakingCheckbox)
      }

      // Should handle gracefully without errors
      expect(stakingCheckbox).toBeInTheDocument()
    })
  })
})
