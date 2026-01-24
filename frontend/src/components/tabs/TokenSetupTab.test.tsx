import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FormProvider, useForm } from 'react-hook-form'
import { TokenSetupTab } from './TokenSetupTab'
import { DEFAULT_CONFIG } from '@/lib/constants'
import type { SimulationConfig } from '@/types/config'

function TokenSetupTabWrapper() {
  const methods = useForm<SimulationConfig>({
    defaultValues: DEFAULT_CONFIG
  })

  return (
    <FormProvider {...methods}>
      <TokenSetupTab />
    </FormProvider>
  )
}

describe('TokenSetupTab', () => {
  it('renders without crashing', () => {
    render(<TokenSetupTabWrapper />)
    expect(screen.getByText('Token Configuration')).toBeInTheDocument()
  })

  it('displays all form fields', () => {
    render(<TokenSetupTabWrapper />)

    expect(screen.getByLabelText('Token Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Total Supply')).toBeInTheDocument()
    expect(screen.getByLabelText('Start Date (TGE)')).toBeInTheDocument()
    expect(screen.getByLabelText('Simulation Horizon (Months)')).toBeInTheDocument()
    expect(screen.getByLabelText('Allocation Mode')).toBeInTheDocument()
    expect(screen.getByLabelText('Simulation Tier')).toBeInTheDocument()
  })

  it('populates default values from DEFAULT_CONFIG', () => {
    render(<TokenSetupTabWrapper />)

    const nameInput = screen.getByLabelText('Token Name') as HTMLInputElement
    expect(nameInput.value).toBe(DEFAULT_CONFIG.token.name)

    const supplyInput = screen.getByLabelText('Total Supply') as HTMLInputElement
    expect(supplyInput.value).toBe(DEFAULT_CONFIG.token.total_supply.toString())
  })

  it('shows tier 2 description when tier 2 is selected', () => {
    function Tier2Wrapper() {
      const methods = useForm<SimulationConfig>({
        defaultValues: {
          ...DEFAULT_CONFIG,
          token: {
            ...DEFAULT_CONFIG.token,
            simulation_mode: 'tier2'
          }
        }
      })

      return (
        <FormProvider {...methods}>
          <TokenSetupTab />
        </FormProvider>
      )
    }

    render(<Tier2Wrapper />)
    expect(screen.getByText(/Tier 2 includes dynamic staking/)).toBeInTheDocument()
  })

  it('shows tier 3 description when tier 3 is selected', () => {
    function Tier3Wrapper() {
      const methods = useForm<SimulationConfig>({
        defaultValues: {
          ...DEFAULT_CONFIG,
          token: {
            ...DEFAULT_CONFIG.token,
            simulation_mode: 'tier3'
          }
        }
      })

      return (
        <FormProvider {...methods}>
          <TokenSetupTab />
        </FormProvider>
      )
    }

    render(<Tier3Wrapper />)
    expect(screen.getByText(/Tier 3 adds Monte Carlo simulation/)).toBeInTheDocument()
  })
})
