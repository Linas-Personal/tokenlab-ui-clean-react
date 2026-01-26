import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { ABMCohortMetric } from '@/types/abm'

interface CohortBehaviorChartProps {
  cohortMetrics: ABMCohortMetric[]
  type?: 'sell' | 'stake' | 'hold' | 'all'
}

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{
    dataKey: string
    value: number
    payload?: any
    name: string
    color: string
  }>
  label?: string | number
}

const COHORT_COLORS: Record<string, string> = {
  Team: '#3b82f6',
  VC: '#8b5cf6',
  Community: '#10b981',
  Investors: '#f59e0b',
  Advisors: '#ef4444',
  Public: '#06b6d4',
  Treasury: '#ec4899',
  Foundation: '#6366f1'
}

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

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (!active || !payload || !payload.length) return null

  return (
    <div className="bg-background border rounded-lg shadow-lg p-3">
      <p className="font-semibold mb-2">Month {label}</p>
      <div className="space-y-1">
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-sm"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm">{entry.name}:</span>
            </div>
            <span className="text-sm font-semibold">{formatNumber(entry.value)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function CohortBehaviorChart({ cohortMetrics, type = 'all' }: CohortBehaviorChartProps) {
  if (!cohortMetrics || cohortMetrics.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Cohort Behavior Analysis</CardTitle>
          <CardDescription>No cohort data available</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-muted-foreground">
            Run a simulation with cohort details enabled to see this chart
          </div>
        </CardContent>
      </Card>
    )
  }

  // Group metrics by month
  const monthlyData: Record<number, any> = {}
  const cohorts = new Set<string>()

  cohortMetrics.forEach(metric => {
    cohorts.add(metric.cohort)

    if (!monthlyData[metric.month_index]) {
      monthlyData[metric.month_index] = {
        month: metric.month_index
      }
    }

    monthlyData[metric.month_index][`${metric.cohort}_sold`] = metric.total_sold
    monthlyData[metric.month_index][`${metric.cohort}_staked`] = metric.total_staked
    monthlyData[metric.month_index][`${metric.cohort}_held`] = metric.total_held
    monthlyData[metric.month_index][`${metric.cohort}_agents`] = metric.num_agents
  })

  const chartData = Object.values(monthlyData).sort((a, b) => a.month - b.month)
  const cohortArray = Array.from(cohorts)

  const renderSellPressureChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="month"
          label={{ value: 'Month', position: 'insideBottom', offset: -5 }}
          className="text-sm"
        />
        <YAxis
          label={{ value: 'Tokens Sold', angle: -90, position: 'insideLeft' }}
          tickFormatter={formatNumber}
          className="text-sm"
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        {cohortArray.map(cohort => (
          <Area
            key={cohort}
            type="monotone"
            dataKey={`${cohort}_sold`}
            name={cohort}
            stackId="1"
            stroke={COHORT_COLORS[cohort] || '#6b7280'}
            fill={COHORT_COLORS[cohort] || '#6b7280'}
            fillOpacity={0.6}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  )

  const renderStakingChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="month"
          label={{ value: 'Month', position: 'insideBottom', offset: -5 }}
          className="text-sm"
        />
        <YAxis
          label={{ value: 'Tokens Staked', angle: -90, position: 'insideLeft' }}
          tickFormatter={formatNumber}
          className="text-sm"
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        {cohortArray.map(cohort => (
          <Bar
            key={cohort}
            dataKey={`${cohort}_staked`}
            name={cohort}
            stackId="1"
            fill={COHORT_COLORS[cohort] || '#6b7280'}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )

  const renderHoldingChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="month"
          label={{ value: 'Month', position: 'insideBottom', offset: -5 }}
          className="text-sm"
        />
        <YAxis
          label={{ value: 'Tokens Held', angle: -90, position: 'insideLeft' }}
          tickFormatter={formatNumber}
          className="text-sm"
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        {cohortArray.map(cohort => (
          <Area
            key={cohort}
            type="monotone"
            dataKey={`${cohort}_held`}
            name={cohort}
            stackId="1"
            stroke={COHORT_COLORS[cohort] || '#6b7280'}
            fill={COHORT_COLORS[cohort] || '#6b7280'}
            fillOpacity={0.6}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  )

  const renderCompositeChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="month"
          label={{ value: 'Month', position: 'insideBottom', offset: -5 }}
          className="text-sm"
        />
        <YAxis
          label={{ value: 'Token Amounts', angle: -90, position: 'insideLeft' }}
          tickFormatter={formatNumber}
          className="text-sm"
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        {cohortArray.map(cohort => (
          <Line
            key={`${cohort}_sold`}
            type="monotone"
            dataKey={`${cohort}_sold`}
            name={`${cohort} (Sold)`}
            stroke={COHORT_COLORS[cohort] || '#6b7280'}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )

  if (type === 'sell') {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Sell Pressure by Cohort</CardTitle>
          <CardDescription>
            Token selling behavior across different cohorts over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          {renderSellPressureChart()}
        </CardContent>
      </Card>
    )
  }

  if (type === 'stake') {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Staking by Cohort</CardTitle>
          <CardDescription>
            Token staking behavior across different cohorts over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          {renderStakingChart()}
        </CardContent>
      </Card>
    )
  }

  if (type === 'hold') {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Holding Patterns by Cohort</CardTitle>
          <CardDescription>
            Token holding behavior across different cohorts over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          {renderHoldingChart()}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cohort Behavior Analysis</CardTitle>
        <CardDescription>
          Detailed breakdown of sell, stake, and hold behavior by cohort
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="sell" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="sell">Sell Pressure</TabsTrigger>
            <TabsTrigger value="stake">Staking</TabsTrigger>
            <TabsTrigger value="hold">Holding</TabsTrigger>
            <TabsTrigger value="all">All Behaviors</TabsTrigger>
          </TabsList>

          <TabsContent value="sell" className="mt-6">
            {renderSellPressureChart()}
            <div className="mt-4 text-sm text-muted-foreground">
              <p>
                Stacked area chart showing cumulative sell pressure from each cohort.
                Higher selling indicates more aggressive liquidation behavior.
              </p>
            </div>
          </TabsContent>

          <TabsContent value="stake" className="mt-6">
            {renderStakingChart()}
            <div className="mt-4 text-sm text-muted-foreground">
              <p>
                Stacked bar chart showing monthly staking amounts by cohort.
                Staking removes tokens from circulation and earns rewards.
              </p>
            </div>
          </TabsContent>

          <TabsContent value="hold" className="mt-6">
            {renderHoldingChart()}
            <div className="mt-4 text-sm text-muted-foreground">
              <p>
                Stacked area chart showing tokens held (not sold or staked) by each cohort.
                Higher holding indicates long-term conviction.
              </p>
            </div>
          </TabsContent>

          <TabsContent value="all" className="mt-6">
            {renderCompositeChart()}
            <div className="mt-4 text-sm text-muted-foreground">
              <p>
                Line chart overlaying sell behavior from all cohorts. Compare relative selling patterns
                to identify which cohorts create the most market pressure.
              </p>
            </div>
          </TabsContent>
        </Tabs>

        <div className="mt-6 pt-6 border-t">
          <h4 className="text-sm font-semibold mb-3">Cohort Summary</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            {cohortArray.map(cohort => {
              const latestData = chartData[chartData.length - 1]
              const sold = latestData[`${cohort}_sold`] || 0
              const staked = latestData[`${cohort}_staked`] || 0
              const held = latestData[`${cohort}_held`] || 0
              const total = sold + staked + held

              return (
                <div key={cohort} className="space-y-1">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-sm"
                      style={{ backgroundColor: COHORT_COLORS[cohort] || '#6b7280' }}
                    />
                    <span className="font-semibold">{cohort}</span>
                  </div>
                  <div className="text-xs text-muted-foreground space-y-0.5 ml-5">
                    <div>Sold: {formatNumber(sold)}</div>
                    <div>Staked: {formatNumber(staked)}</div>
                    <div>Held: {formatNumber(held)}</div>
                    <div className="font-semibold">Total: {formatNumber(total)}</div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
