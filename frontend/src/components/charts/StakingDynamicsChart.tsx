import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { GlobalMetric } from '@/types/simulation'
import { formatTokens, formatPercentage } from '@/lib/utils'

interface StakingDynamicsChartProps {
  data: GlobalMetric[]
}

const CustomTooltip = ({ active, payload, label }: TooltipProps<number, string>) => {
  if (!active || !payload || !payload.length) return null

  const staked = payload.find(p => p.dataKey === 'staked_amount')
  const liquidity = payload.find(p => p.dataKey === 'liquidity_deployed')

  return (
    <div className="bg-background border rounded-lg shadow-lg p-3">
      <p className="font-semibold mb-2">Month {label}</p>
      <div className="space-y-1">
        {staked && staked.value && (
          <div className="flex items-center justify-between gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: staked.color }} />
              <span>Staked:</span>
            </div>
            <span className="font-medium">{formatTokens(staked.value)}</span>
          </div>
        )}
        {liquidity && liquidity.value && (
          <div className="flex items-center justify-between gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: liquidity.color }} />
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
