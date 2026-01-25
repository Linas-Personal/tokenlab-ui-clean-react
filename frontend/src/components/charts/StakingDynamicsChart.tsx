import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { GlobalMetric } from '@/types/simulation'
import { formatTokens, formatPercentage } from '@/lib/utils'

interface StakingDynamicsChartProps {
  data: GlobalMetric[]
}

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{
    dataKey: string
    value: number
    color: string
    payload?: any
  }>
  label?: string | number
}

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (!active || !payload || !payload.length) return null

  const staked = payload.find(p => p.dataKey === 'staked_amount')
  const liquidity = payload.find(p => p.dataKey === 'liquidity_deployed')

  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg shadow-lg p-3">
      <p className="font-semibold mb-2 text-slate-900 dark:text-slate-100">Month {label}</p>
      <div className="space-y-1">
        {staked && staked.value && (
          <div className="flex items-center justify-between gap-4 text-sm text-slate-700 dark:text-slate-200">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-purple-500" />
              <span>Staked:</span>
            </div>
            <span className="font-medium">{formatTokens(staked.value)}</span>
          </div>
        )}
        {liquidity && liquidity.value && (
          <div className="flex items-center justify-between gap-4 text-sm text-slate-700 dark:text-slate-200">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-cyan-500" />
              <span>Liquidity:</span>
            </div>
            <span className="font-medium">{formatTokens(liquidity.value)}</span>
          </div>
        )}
      </div>
    </div>
  )
}

export function StakingDynamicsChart({ data }: StakingDynamicsChartProps) {
  const stakingData = data.filter(d => d.staked_amount !== null && d.staked_amount !== undefined)

  if (stakingData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Staking Dynamics</CardTitle>
          <CardDescription>Available in Tier 2/3 simulations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[400px] flex items-center justify-center text-muted-foreground">
            No staking data available (Tier 1 mode or staking disabled)
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Staking & Liquidity Dynamics</CardTitle>
        <CardDescription>
          Staked tokens and liquidity deployment over time (Tier 2/3)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={stakingData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="month_index"
              label={{ value: 'Month', position: 'insideBottom', offset: -5 }}
              className="text-xs"
            />
            <YAxis
              label={{ value: 'Tokens', angle: -90, position: 'insideLeft' }}
              tickFormatter={(value) => formatTokens(value)}
              className="text-xs"
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar dataKey="staked_amount" fill="#8b5cf6" name="Staked Tokens" />
            <Line
              type="monotone"
              dataKey="liquidity_deployed"
              stroke="#06b6d4"
              strokeWidth={2.5}
              name="Liquidity Deployed"
              dot={{ r: 3 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
