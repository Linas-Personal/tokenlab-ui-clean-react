import { useFormContext } from 'react-hook-form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { SimulationConfig } from '@/types/config'

export function TokenSetupTab() {
  const { register, watch } = useFormContext<SimulationConfig>()
  const simulationMode = watch('token.simulation_mode')

  return (
    <Card>
      <CardHeader>
        <CardTitle>Token Configuration</CardTitle>
        <CardDescription>
          Define basic token parameters and simulation settings
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="token-name">Token Name</Label>
            <Input id="token-name" {...register('token.name')} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="total-supply">Total Supply</Label>
            <Input
              id="total-supply"
              type="number"
              {...register('token.total_supply', { valueAsNumber: true })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="start-date">Start Date (TGE)</Label>
            <Input id="start-date" type="date" {...register('token.start_date')} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="horizon-months">Simulation Horizon (Months)</Label>
            <Input
              id="horizon-months"
              type="number"
              {...register('token.horizon_months', { valueAsNumber: true })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="allocation-mode">Allocation Mode</Label>
            <select
              id="allocation-mode"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              {...register('token.allocation_mode')}
            >
              <option value="percent">Percentage</option>
              <option value="tokens">Token Amounts</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="simulation-mode">Simulation Tier</Label>
            <select
              id="simulation-mode"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              {...register('token.simulation_mode')}
            >
              <option value="tier1">Tier 1 - Basic Vesting</option>
              <option value="tier2">Tier 2 - Dynamic Market</option>
              <option value="tier3">Tier 3 - Monte Carlo</option>
            </select>
          </div>
        </div>

        {simulationMode !== 'tier1' && (
          <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-md border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-900 dark:text-blue-100">
              {simulationMode === 'tier2' &&
                'Tier 2 includes dynamic staking, pricing models, treasury strategies, and volume calculation.'}
              {simulationMode === 'tier3' &&
                'Tier 3 adds Monte Carlo simulation with multiple trials and cohort-based behavior modeling.'}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
