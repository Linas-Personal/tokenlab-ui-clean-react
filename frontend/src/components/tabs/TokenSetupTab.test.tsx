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
  })

  it('populates default values from DEFAULT_CONFIG', () => {
    render(<TokenSetupTabWrapper />)

    const nameInput = screen.getByLabelText('Token Name') as HTMLInputElement
    expect(nameInput.value).toBe(DEFAULT_CONFIG.token.name)

    const supplyInput = screen.getByLabelText('Total Supply') as HTMLInputElement
    expect(supplyInput.value).toBe(DEFAULT_CONFIG.token.total_supply.toString())
  })

  it('shows ABM simulation description', () => {
    render(<TokenSetupTabWrapper />)
    expect(screen.getByText(/Agent-Based Modeling.*ABM.*Simulation/)).toBeInTheDocument()
  })

  it('sets simulation_mode to abm by default', () => {
    render(<TokenSetupTabWrapper />)
    const hiddenInput = document.querySelector('input[type="hidden"]') as HTMLInputElement
    expect(hiddenInput).toBeTruthy()
    expect(hiddenInput.value).toBe('abm')
  })
})
