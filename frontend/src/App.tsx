import { useState } from 'react'
import { useForm, FormProvider, useFormContext } from 'react-hook-form'
import { useMutation } from '@tanstack/react-query'
import { Coins, Calendar, Settings, Rocket, BarChart3, Loader2 } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { DEFAULT_CONFIG } from '@/lib/constants'
import { api } from '@/lib/api'
import type { SimulationConfig } from '@/types/config'
import type { SimulationResponse } from '@/types/simulation'
import { formatTokens, formatPercentage } from '@/lib/utils'

function App() {
  const [activeTab, setActiveTab] = useState('token-setup')
  const methods = useForm<SimulationConfig>({
    defaultValues: DEFAULT_CONFIG
  })

  const simulation = useMutation({
    mutationFn: (config: SimulationConfig) => api.runSimulation(config),
    onSuccess: () => {
      setActiveTab('results')
    }
  })

  const onSubmit = (data: SimulationConfig) => {
    simulation.mutate(data)
  }

  const handleRunSimulation = () => {
    methods.handleSubmit(onSubmit)()
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Token Vesting Simulator</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Model token unlock schedules and market dynamics
              </p>
            </div>
            <div className="text-sm text-muted-foreground">
              Powered by TokenLab
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        <FormProvider {...methods}>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-5 mb-8">
              <TabsTrigger value="token-setup" className="flex items-center gap-2">
                <Coins className="h-4 w-4" />
                <span className="hidden sm:inline">Token Setup</span>
              </TabsTrigger>
              <TabsTrigger value="vesting" className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                <span className="hidden sm:inline">Vesting Schedule</span>
              </TabsTrigger>
              <TabsTrigger value="assumptions" className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                <span className="hidden sm:inline">Assumptions</span>
              </TabsTrigger>
              <TabsTrigger value="advanced" className="flex items-center gap-2">
                <Rocket className="h-4 w-4" />
                <span className="hidden sm:inline">Advanced</span>
              </TabsTrigger>
              <TabsTrigger value="results" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                <span className="hidden sm:inline">Results</span>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="token-setup">
              <TokenSetupTab />
            </TabsContent>

            <TabsContent value="vesting">
              <VestingScheduleTab />
            </TabsContent>

            <TabsContent value="assumptions">
              <AssumptionsTab />
            </TabsContent>

            <TabsContent value="advanced">
              <AdvancedTab />
            </TabsContent>

            <TabsContent value="results">
              <ResultsTab
                simulation={simulation.data}
                isLoading={simulation.isPending}
                onRunSimulation={handleRunSimulation}
              />
            </TabsContent>
          </Tabs>
        </FormProvider>

        <div className="mt-8 flex justify-end gap-4">
          <Button
            size="lg"
            onClick={handleRunSimulation}
            disabled={simulation.isPending}
          >
            {simulation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Running Simulation...
              </>
            ) : (
              <>
                <BarChart3 className="mr-2 h-4 w-4" />
                Run Simulation
              </>
            )}
          </Button>
        </div>
      </main>
    </div>
  )
}

function TokenSetupTab() {
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

function VestingScheduleTab() {
  const { register, watch } = useFormContext<SimulationConfig>()
  const buckets = watch('buckets') || DEFAULT_CONFIG.buckets

  return (
    <Card>
      <CardHeader>
        <CardTitle>Vesting Schedule</CardTitle>
        <CardDescription>
          Configure unlock schedules for each bucket
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Bucket</th>
                <th className="text-left p-2">Allocation</th>
                <th className="text-left p-2">TGE %</th>
                <th className="text-left p-2">Cliff (mo)</th>
                <th className="text-left p-2">Vesting (mo)</th>
              </tr>
            </thead>
            <tbody>
              {buckets.map((bucket, index) => (
                <tr key={index} className="border-b">
                  <td className="p-2">
                    <Input {...register(`buckets.${index}.bucket`)} />
                  </td>
                  <td className="p-2">
                    <Input
                      type="number"
                      {...register(`buckets.${index}.allocation`, { valueAsNumber: true })}
                    />
                  </td>
                  <td className="p-2">
                    <Input
                      type="number"
                      {...register(`buckets.${index}.tge_unlock_pct`, { valueAsNumber: true })}
                    />
                  </td>
                  <td className="p-2">
                    <Input
                      type="number"
                      {...register(`buckets.${index}.cliff_months`, { valueAsNumber: true })}
                    />
                  </td>
                  <td className="p-2">
                    <Input
                      type="number"
                      {...register(`buckets.${index}.vesting_months`, { valueAsNumber: true })}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}

function AssumptionsTab() {
  const { register } = useFormContext<SimulationConfig>()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Market Assumptions & Behaviors</CardTitle>
        <CardDescription>
          Configure base assumptions and behavioral modifiers
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="sell-pressure">Base Sell Pressure Level</Label>
            <select
              id="sell-pressure"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              {...register('assumptions.sell_pressure_level')}
            >
              <option value="low">Low (10%)</option>
              <option value="medium">Medium (25%)</option>
              <option value="high">High (50%)</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="daily-volume">Average Daily Volume (tokens)</Label>
            <Input
              id="daily-volume"
              type="number"
              placeholder="Optional"
              {...register('assumptions.avg_daily_volume_tokens', { valueAsNumber: true })}
            />
          </div>
        </div>

        <Accordion type="multiple" className="w-full">
          <AccordionItem value="cliff-shock">
            <AccordionTrigger>Cliff Shock Behavior</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="cliff-shock-enabled"
                    className="h-4 w-4"
                    {...register('behaviors.cliff_shock.enabled')}
                  />
                  <Label htmlFor="cliff-shock-enabled">
                    Enable increased selling at cliff unlock
                  </Label>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cliff-multiplier">Sell Pressure Multiplier</Label>
                  <Input
                    id="cliff-multiplier"
                    type="number"
                    step="0.1"
                    {...register('behaviors.cliff_shock.multiplier', { valueAsNumber: true })}
                  />
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="relock">
            <AccordionTrigger>Relock / Staking Delay</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="relock-enabled"
                    className="h-4 w-4"
                    {...register('behaviors.relock.enabled')}
                  />
                  <Label htmlFor="relock-enabled">
                    Enable token relocking after unlock
                  </Label>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="relock-pct">Relock Percentage</Label>
                    <Input
                      id="relock-pct"
                      type="number"
                      step="0.01"
                      {...register('behaviors.relock.relock_pct', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lock-duration">Lock Duration (months)</Label>
                    <Input
                      id="lock-duration"
                      type="number"
                      {...register('behaviors.relock.lock_duration_months', { valueAsNumber: true })}
                    />
                  </div>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  )
}

function AdvancedTab() {
  const { watch } = useFormContext<SimulationConfig>()
  const simulationMode = watch('token.simulation_mode')

  if (simulationMode === 'tier1') {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Advanced Features</CardTitle>
          <CardDescription>
            Available in Tier 2 and Tier 3 modes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Rocket className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Switch to Tier 2 or Tier 3 in Token Setup to access advanced features like
              dynamic staking, pricing models, treasury strategies, and Monte Carlo simulation.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Advanced Configuration - {simulationMode === 'tier2' ? 'Tier 2' : 'Tier 3'}</CardTitle>
        <CardDescription>
          Configure advanced market dynamics and simulation parameters
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8 text-muted-foreground">
          Advanced tier configuration panel (Tier 2/3 features)
        </div>
      </CardContent>
    </Card>
  )
}

interface ResultsTabProps {
  simulation?: SimulationResponse
  isLoading: boolean
  onRunSimulation: () => void
}

function ResultsTab({ simulation, isLoading, onRunSimulation }: ResultsTabProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-24">
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" />
            <p className="text-lg font-medium">Running simulation...</p>
            <p className="text-sm text-muted-foreground mt-2">
              Calculating vesting schedules and market dynamics
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!simulation) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-24">
          <div className="text-center">
            <BarChart3 className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">No simulation results yet</p>
            <p className="text-sm text-muted-foreground mb-6">
              Configure your token parameters and click "Run Simulation" to see results
            </p>
            <Button size="lg" onClick={onRunSimulation}>
              <BarChart3 className="mr-2 h-4 w-4" />
              Run Simulation
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  const { summary_cards } = simulation.data

  return (
    <div className="space-y-6">
      {simulation.warnings.length > 0 && (
        <Card className="border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-950">
          <CardHeader>
            <CardTitle className="text-yellow-900 dark:text-yellow-100">Warnings</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-1">
              {simulation.warnings.map((warning, i) => (
                <li key={i} className="text-sm text-yellow-900 dark:text-yellow-100">{warning}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Max Monthly Unlock</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{formatTokens(summary_cards.max_unlock_tokens)}</p>
            <p className="text-sm text-muted-foreground mt-1">
              Month {summary_cards.max_unlock_month}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Max Monthly Sell</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{formatTokens(summary_cards.max_sell_tokens)}</p>
            <p className="text-sm text-muted-foreground mt-1">
              Month {summary_cards.max_sell_month}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Circulating Supply</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">12 months:</span>
                <span className="font-semibold">{formatPercentage(summary_cards.circ_12_pct)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">24 months:</span>
                <span className="font-semibold">{formatPercentage(summary_cards.circ_24_pct)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">End:</span>
                <span className="font-semibold">{formatPercentage(summary_cards.circ_end_pct)}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Simulation Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Execution Time</p>
              <p className="font-medium">{simulation.execution_time_ms.toFixed(2)} ms</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Data Points</p>
              <p className="font-medium">{simulation.data.bucket_results.length} rows</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default App
