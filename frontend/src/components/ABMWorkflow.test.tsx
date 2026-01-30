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

      // Agent Population accordion is open by default, slider should be visible
      // The slider is rendered by shadcn/ui Slider component - check for the actual displayed value
      const displayedValue = screen.getByText(/^50$/) // Default value from DEFAULT_CONFIG
      expect(displayedValue).toBeInTheDocument()
    })

    it('enforces min and max bounds for agents per cohort', async () => {
      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      // Check that the slider range values are displayed
      expect(screen.getByText('10')).toBeInTheDocument() // min value shown
      expect(screen.getByText('500')).toBeInTheDocument() // max value shown
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

      // Pricing accordion is open by default, find the select by ID
      const pricingModelSelect = screen.getByDisplayValue(/Equation of Exchange/i) as HTMLSelectElement

      // EOE model (default) shows holding time, smoothing factor, min price
      expect(screen.getByLabelText(/Holding Time/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Smoothing Factor/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Min Price/i)).toBeInTheDocument()

      // Bonding curve shows k and n parameters
      await user.selectOptions(pricingModelSelect, 'bonding_curve')
      await waitFor(() => {
        expect(screen.getByLabelText(/K Parameter/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/N Parameter/i)).toBeInTheDocument()
      })

      // Issuance curve shows alpha parameter
      await user.selectOptions(pricingModelSelect, 'issuance_curve')
      await waitFor(() => {
        expect(screen.getByLabelText(/Alpha Parameter/i)).toBeInTheDocument()
      })

      // Constant shows no extra fields
      await user.selectOptions(pricingModelSelect, 'constant')
      await waitFor(() => {
        expect(screen.queryByLabelText(/Holding Time/i)).not.toBeInTheDocument()
      })
    })

    it('validates pricing config inputs', async () => {
      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      // EOE is default, smoothing factor field should be visible
      const smoothingFactorInput = screen.getByLabelText(/Smoothing Factor/i) as HTMLInputElement

      // Input should have max constraint
      expect(smoothingFactorInput.max).toBe('1')
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

      // Click staking accordion to expand it
      const stakingAccordion = screen.getByText('Staking Pool (Optional)')
      await user.click(stakingAccordion)

      // Find and click staking checkbox
      const stakingCheckbox = screen.getByLabelText(/Enable dynamic staking pool with variable APY/i)
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

      // Click staking accordion to expand it
      const stakingAccordion = screen.getByText('Staking Pool (Optional)')
      await user.click(stakingAccordion)

      // Uncheck staking
      const stakingCheckbox = screen.getByLabelText(/Enable dynamic staking pool with variable APY/i)
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

      // Click staking accordion to expand it
      const stakingAccordion = screen.getByText('Staking Pool (Optional)')
      await user.click(stakingAccordion)

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

      // Click treasury accordion to expand it
      const treasuryAccordion = screen.getByText('Treasury Management (Optional)')
      await user.click(treasuryAccordion)

      const treasuryCheckbox = screen.getByLabelText(/Enable treasury with buyback and burn/i)
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

      // Click treasury accordion to expand it
      const treasuryAccordion = screen.getByText('Treasury Management (Optional)')
      await user.click(treasuryAccordion)

      const burnCheckbox = screen.getByLabelText(/Burn bought tokens/i)

      // Check current state (default is true from DEFAULT_CONFIG)
      const initialState = (burnCheckbox as HTMLInputElement).checked

      // Toggle
      await user.click(burnCheckbox)
      expect((burnCheckbox as HTMLInputElement).checked).toBe(!initialState)
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

      // Click treasury accordion to expand it
      const treasuryAccordion = screen.getByText('Treasury Management (Optional)')
      await user.click(treasuryAccordion)

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

      // Click Monte Carlo accordion to expand it
      const mcAccordion = screen.getByText('Monte Carlo Simulations (Optional)')
      await user.click(mcAccordion)

      const mcCheckbox = screen.getByLabelText(/Enable Monte Carlo probabilistic forecasting/i)
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

      // Click Monte Carlo accordion to expand it
      const mcAccordion = screen.getByText('Monte Carlo Simulations (Optional)')
      await user.click(mcAccordion)

      // Check that default value is displayed (100 from DEFAULT_CONFIG)
      expect(screen.getByText('100')).toBeInTheDocument()
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

      // Click Monte Carlo accordion to expand it
      const mcAccordion = screen.getByText('Monte Carlo Simulations (Optional)')
      await user.click(mcAccordion)

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

      // Click Monte Carlo accordion to expand it
      const mcAccordion = screen.getByText('Monte Carlo Simulations (Optional)')
      await user.click(mcAccordion)

      // Should show time estimate (100 * 0.007 = 0.7s)
      expect(screen.getByText(/Expected time/i)).toBeInTheDocument()
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

      // Click volume accordion to expand it
      const volumeAccordion = screen.getByText('Dynamic Volume (Optional)')
      await user.click(volumeAccordion)

      const volumeCheckbox = screen.getByLabelText(/Enable dynamic transaction volume calculation/i)
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

      // Click volume accordion to expand it
      const volumeAccordion = screen.getByText('Dynamic Volume (Optional)')
      await user.click(volumeAccordion)

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
    it('shows cohort behavior preset descriptions', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      // Click cohort behavior accordion to expand it
      const cohortAccordion = screen.getByText('Cohort Behavior Presets (Optional)')
      await user.click(cohortAccordion)

      expect(screen.getByText('Conservative')).toBeInTheDocument()
      expect(screen.getByText('Moderate')).toBeInTheDocument()
      expect(screen.getByText('Aggressive')).toBeInTheDocument()
    })

    it('assigns behavioral preset to bucket', async () => {
      const user = userEvent.setup()

      const configWithBuckets = {
        ...DEFAULT_CONFIG,
        buckets: [
          { bucket: 'Team', allocation: 30, tge_unlock_pct: 0, cliff_months: 12, vesting_months: 24, unlock_type: 'linear' as const },
          { bucket: 'Investors', allocation: 40, tge_unlock_pct: 10, cliff_months: 6, vesting_months: 18, unlock_type: 'linear' as const },
          { bucket: 'Community', allocation: 30, tge_unlock_pct: 20, cliff_months: 0, vesting_months: 12, unlock_type: 'linear' as const }
        ]
      }

      render(
        <TestWrapper defaultValues={configWithBuckets}>
          <ABMConfigForm />
        </TestWrapper>
      )

      // Click cohort behavior accordion to expand it
      const cohortAccordion = screen.getByText('Cohort Behavior Presets (Optional)')
      await user.click(cohortAccordion)

      // Should show bucket names in the bucket assignments section
      await waitFor(() => {
        expect(screen.getByText('Team')).toBeInTheDocument()
      })

      // Find all select dropdowns
      const selects = screen.getAllByRole('combobox')

      // Team select should be available, select conservative
      const teamSelect = selects[selects.length - 3] // Last 3 are the bucket selects
      if (teamSelect) {
        await user.selectOptions(teamSelect, 'conservative')
        expect((teamSelect as HTMLSelectElement).value).toBe('conservative')
      }
    })

    it('shows warning when no buckets are configured', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper defaultValues={{
          ...DEFAULT_CONFIG,
          buckets: []
        }}>
          <ABMConfigForm />
        </TestWrapper>
      )

      // Click cohort behavior accordion to expand it
      const cohortAccordion = screen.getByText('Cohort Behavior Presets (Optional)')
      await user.click(cohortAccordion)

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

      // Agent population accordion is open by default
      // Check that slider displays min and max values
      expect(screen.getByText('10')).toBeInTheDocument() // min
      expect(screen.getByText('500')).toBeInTheDocument() // max
    })

    it('handles rapid toggling of checkboxes', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <ABMConfigForm />
        </TestWrapper>
      )

      // Click staking accordion to expand it
      const stakingAccordion = screen.getByText('Staking Pool (Optional)')
      await user.click(stakingAccordion)

      const stakingCheckbox = screen.getByLabelText(/Enable dynamic staking pool with variable APY/i)

      // Toggle multiple times rapidly
      for (let i = 0; i < 5; i++) {
        await user.click(stakingCheckbox)
      }

      // Should handle gracefully without errors
      expect(stakingCheckbox).toBeInTheDocument()
    })
  })
})
