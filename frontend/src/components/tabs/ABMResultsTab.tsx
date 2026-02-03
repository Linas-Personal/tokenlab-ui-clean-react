import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Play, XCircle, CheckCircle2, Info } from 'lucide-react'
import { JobStatusDisplay } from '@/components/JobStatusDisplay'
import { ProgressBarSSE } from '@/components/ProgressBarSSE'
import { StakingMetricsDisplay } from '@/components/StakingMetricsDisplay'
import { TreasuryMetricsDisplay } from '@/components/TreasuryMetricsDisplay'
import { CohortBehaviorChart } from '@/components/charts/CohortBehaviorChart'
import { PriceEvolutionChart } from '@/components/charts/PriceEvolutionChart'
import { CirculatingSupplyChart } from '@/components/charts/CirculatingSupplyChart'
import { SellPressureChart } from '@/components/charts/SellPressureChart'
import { useJobPolling } from '@/hooks/useJobPolling'
import type { JobStatusResponse } from '@/types/abm'
import { hasStakingMetrics, hasTreasuryMetrics } from '@/types/abm'
import type { UseABMSimulationReturn } from '@/hooks/useABMSimulation'

interface ABMResultsTabProps {
  simulation: UseABMSimulationReturn
  onRunSimulation?: () => void
}

export function ABMResultsTab({ simulation, onRunSimulation }: ABMResultsTabProps) {
  const {
    isSubmitting,
    isRunning,
    isCompleted,
    isFailed,
    error,
    jobId,
    results,
    cached,
    fetchResults
  } = simulation

  const {
    status: jobStatus,
    isPolling
  } = useJobPolling(jobId, {
    enabled: isRunning,
    pollInterval: 1000,
    onComplete: async (status: JobStatusResponse) => {
      if (status.status === 'completed') {
        await fetchResults()
      }
    }
  })

  useEffect(() => {
    if (jobId && jobStatus?.status === 'completed' && !results) {
      fetchResults()
    }
  }, [jobId, jobStatus, results, fetchResults])

  const formatNumber = (num: number): string => {
    if (num >= 1_000_000_000) {
      return `${(num / 1_000_000_000).toFixed(2)}B`
    } else if (num >= 1_000_000) {
      return `${(num / 1_000_000).toFixed(2)}M`
    } else if (num >= 1_000) {
      return `${(num / 1_000).toFixed(2)}K`
    }
    return num.toFixed(2)
  }

  const renderEmptyState = () => (
    <Card>
      <CardHeader>
        <CardTitle>ABM Simulation Results</CardTitle>
        <CardDescription>
          Run an Agent-Based Model simulation to see results
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
            <Play className="h-8 w-8 text-muted-foreground" />
          </div>
          <div className="text-center space-y-2">
            <p className="text-lg font-semibold">No simulation results yet</p>
            <p className="text-sm text-muted-foreground max-w-md">
              Configure your ABM settings in the previous tabs and click "Run ABM Simulation"
              to start a simulation with individual token holder agents.
            </p>
          </div>
          {onRunSimulation && (
            <Button onClick={onRunSimulation} size="lg" className="mt-4">
              <Play className="mr-2 h-4 w-4" />
              Run ABM Simulation
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )

  const renderErrorState = () => (
    <Card>
      <CardHeader>
        <CardTitle>Simulation Failed</CardTitle>
        <CardDescription>
          An error occurred during the simulation
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        {onRunSimulation && (
          <div className="mt-6 flex justify-center">
            <Button onClick={onRunSimulation} variant="outline">
              Try Again
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )

  const renderLoadingState = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>ABM Simulation Running</CardTitle>
          <CardDescription>
            {cached ? 'Loading cached results...' : 'Processing individual agent decisions...'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {jobId && jobStatus && (
            <JobStatusDisplay
              jobId={jobId}
              status={jobStatus.status}
              progressPct={jobStatus.progress_pct}
              currentMonth={jobStatus.current_month}
              totalMonths={jobStatus.total_months}
              errorMessage={jobStatus.error_message}
              createdAt={jobStatus.created_at}
            />
          )}

          {jobId && (
            <ProgressBarSSE jobId={jobId} enabled={!cached} showDetails />
          )}

          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription className="text-xs">
              The ABM simulation creates individual agents for each cohort, each with unique behaviors.
              Agents make autonomous selling, staking, and holding decisions based on price movements
              and their individual characteristics.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  )

  const renderResults = () => {
    if (!results) return null

    const globalMetricsFormatted = results.global_metrics.map(m => ({
      month_index: m.month_index,
      date: m.date,
      current_price: m.price,
      total_unlocked: m.total_unlocked,
      total_expected_sell: m.total_sold,
      expected_circulating_total: m.circulating_supply,
      expected_circulating_pct: (m.circulating_supply / results.summary.final_circulating_supply) * 100,
      total_staked: m.total_staked
    }))

    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>ABM Simulation Complete</CardTitle>
                <CardDescription>
                  {cached && 'Cached result - '}
                  Completed in {results.execution_time_seconds.toFixed(2)}s
                </CardDescription>
              </div>
              <CheckCircle2 className="h-8 w-8 text-green-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Final Price</p>
                <p className="text-2xl font-bold">${results.summary.final_price.toFixed(4)}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Final Supply</p>
                <p className="text-2xl font-bold">{formatNumber(results.summary.final_circulating_supply)}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Total Sold</p>
                <p className="text-2xl font-bold">{formatNumber(results.summary.total_sold_cumulative)}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Avg Price</p>
                <p className="text-2xl font-bold">${(results.global_metrics.reduce((sum, m) => sum + m.price, 0) / results.global_metrics.length).toFixed(4)}</p>
              </div>
            </div>

            {results.config && (
              <div className="mt-6 pt-6 border-t">
                <h4 className="text-sm font-semibold mb-3">Simulation Configuration</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Agents:</span>
                    <span className="font-semibold">{results.config.num_agents}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Pricing Model:</span>
                    <span className="font-semibold">{results.config.pricing_model.toUpperCase()}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Staking:</span>
                    <span className="font-semibold">{results.config.has_staking ? 'Enabled' : 'Disabled'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Treasury:</span>
                    <span className="font-semibold">{results.config.has_treasury ? 'Enabled' : 'Disabled'}</span>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Tabs defaultValue="charts" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="charts">Market Dynamics</TabsTrigger>
            <TabsTrigger value="cohorts">Cohort Analysis</TabsTrigger>
            {hasStakingMetrics(results.summary) && <TabsTrigger value="staking">Staking</TabsTrigger>}
            {hasTreasuryMetrics(results.summary) && <TabsTrigger value="treasury">Treasury</TabsTrigger>}
          </TabsList>

          <TabsContent value="charts" className="space-y-6 mt-6">
            <PriceEvolutionChart data={globalMetricsFormatted} />
            <CirculatingSupplyChart data={globalMetricsFormatted} />
            <SellPressureChart data={globalMetricsFormatted} />
          </TabsContent>

          <TabsContent value="cohorts" className="space-y-6 mt-6">
            {results.cohort_metrics && results.cohort_metrics.length > 0 ? (
              <CohortBehaviorChart cohortMetrics={results.cohort_metrics} />
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle>Cohort Analysis</CardTitle>
                  <CardDescription>
                    Cohort details were not stored for this simulation
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription>
                      Enable "Store cohort details" in the ABM configuration to see
                      detailed cohort-level behavior analysis.
                    </AlertDescription>
                  </Alert>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {hasStakingMetrics(results.summary) && (
            <TabsContent value="staking" className="space-y-6 mt-6">
              <StakingMetricsDisplay metrics={results.summary.staking_metrics!} />
            </TabsContent>
          )}

          {hasTreasuryMetrics(results.summary) && (
            <TabsContent value="treasury" className="space-y-6 mt-6">
              <TreasuryMetricsDisplay metrics={results.summary.treasury_metrics!} />
            </TabsContent>
          )}
        </Tabs>

        {results.warnings && results.warnings.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Warnings</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                {results.warnings.map((warning, index) => (
                  <li key={index}>{warning}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>
    )
  }

  if (!jobId && !results) {
    return renderEmptyState()
  }

  if (isFailed) {
    return renderErrorState()
  }

  if (isSubmitting || isRunning || isPolling) {
    return renderLoadingState()
  }

  if (isCompleted && results) {
    return renderResults()
  }

  return renderEmptyState()
}
