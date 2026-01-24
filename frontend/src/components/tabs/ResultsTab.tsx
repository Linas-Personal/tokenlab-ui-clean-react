import { Loader2, BarChart3 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { formatTokens, formatPercentage } from '@/lib/utils'
import { UnlockScheduleChart } from '@/components/charts/UnlockScheduleChart'
import { CirculatingSupplyChart } from '@/components/charts/CirculatingSupplyChart'
import { SellPressureChart } from '@/components/charts/SellPressureChart'
import { PriceEvolutionChart } from '@/components/charts/PriceEvolutionChart'
import { StakingDynamicsChart } from '@/components/charts/StakingDynamicsChart'
import { ExportButtons } from '@/components/results/ExportButtons'
import type { SimulationResponse } from '@/types/simulation'

interface ResultsTabProps {
  simulation?: SimulationResponse
  isLoading: boolean
  onRunSimulation: () => void
}

export function ResultsTab({ simulation, isLoading, onRunSimulation }: ResultsTabProps) {
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

      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">Visualization & Analysis</h3>
          <p className="text-sm text-muted-foreground">
            Execution time: {simulation.execution_time_ms.toFixed(2)} ms |
            Data points: {simulation.data.bucket_results.length} rows
          </p>
        </div>
        <ExportButtons simulation={simulation} />
      </div>

      <UnlockScheduleChart data={simulation.data.bucket_results} />
      <CirculatingSupplyChart data={simulation.data.global_metrics} />
      <SellPressureChart data={simulation.data.global_metrics} />
      <PriceEvolutionChart data={simulation.data.global_metrics} />
      <StakingDynamicsChart data={simulation.data.global_metrics} />
    </div>
  )
}
