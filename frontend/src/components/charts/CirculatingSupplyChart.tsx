import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  TooltipProps
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { GlobalMetric } from '@/types/simulation'
import { formatTokens, formatPercentage } from '@/lib/utils'

interface CirculatingSupplyChartProps {
  data: GlobalMetric[]
}

const CustomTooltip = ({ active, payload, label }: TooltipProps<number, string>) => {
  if (!active || !payload || !payload.length) return null

  const tokens = payload.find(p => p.dataKey === 'expected_circulating_total')
  const percentage = payload.find(p => p.dataKey === 'expected_circulating_pct')

  return (
    <div className="bg-background border rounded-lg shadow-lg p-3">
      <p className="font-semibold mb-2">Month {label}</p>
      <div className="space-y-1">
        {tokens && (
          <div className="flex items-center justify-between gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: tokens.color }} />
              <span>Circulating:</span>
            </div>
            <span className="font-medium">{formatTokens(tokens.value || 0)}</span>
          </div>
        )}
        {percentage && (
          <div className="flex items-center justify-between gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: percentage.color }} />
              <span>% of Supply:</span>
            </div>
            <span className="font-medium">{formatPercentage(percentage.value || 0)}</span>
          </div>
        )}
      </div>
    </div>
  )
}

export function CirculatingSupplyChart({ data }: CirculatingSupplyChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Expected Circulating Supply Over Time</CardTitle>
        <CardDescription>
          Cumulative tokens expected to be circulating (unlocked - relocked)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={data} margin={{ top: 20, right: 60, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="month_index"
              label={{ value: 'Month', position: 'insideBottom', offset: -5 }}
              className="text-xs"
            />
            <YAxis
              yAxisId="left"
              label={{ value: 'Circulating Supply (Tokens)', angle: -90, position: 'insideLeft' }}
              tickFormatter={(value) => formatTokens(value)}
              className="text-xs"
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              label={{ value: '% of Total Supply', angle: 90, position: 'insideRight' }}
              domain={[0, 100]}
              className="text-xs"
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="expected_circulating_total"
              fill="#3b82f6"
              fillOpacity={0.2}
              stroke="none"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="expected_circulating_total"
              stroke="#3b82f6"
              strokeWidth={2.5}
              name="Circulating Tokens"
              dot={false}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="expected_circulating_pct"
              stroke="#8b5cf6"
              strokeWidth={2}
              strokeDasharray="5 5"
              name="% of Supply"
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
