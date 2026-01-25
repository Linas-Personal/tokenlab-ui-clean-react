import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { GlobalMetric } from '@/types/simulation'
import { formatTokens, formatPercentage } from '@/lib/utils'

interface CirculatingSupplyChartProps {
  data: GlobalMetric[]
}

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{
    dataKey: string
    value: number
    color: string
    name: string
  }>
  label?: string | number
}

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (!active || !payload || !payload.length) return null

  // Check if we have Monte Carlo data
  const hasMC = payload.some(p => p.dataKey.includes('_p10') || p.dataKey.includes('_p90') || p.dataKey.includes('_median'))

  if (hasMC) {
    const p10 = payload.find(p => p.dataKey === 'expected_circulating_total_p10')
    const median = payload.find(p => p.dataKey === 'expected_circulating_total_median')
    const p90 = payload.find(p => p.dataKey === 'expected_circulating_total_p90')
    const percentage = payload.find(p => p.dataKey === 'expected_circulating_pct')

    return (
      <div className="bg-background border rounded-lg shadow-lg p-3">
        <p className="font-semibold mb-2">Month {label}</p>
        <div className="space-y-1">
          {median && (
            <div className="flex items-center justify-between gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-blue-500" />
                <span>Median:</span>
              </div>
              <span className="font-medium">{formatTokens(median.value || 0)}</span>
            </div>
          )}
          {p10 && (
            <div className="flex items-center justify-between gap-4 text-sm text-muted-foreground">
              <span className="ml-5">P10:</span>
              <span>{formatTokens(p10.value || 0)}</span>
            </div>
          )}
          {p90 && (
            <div className="flex items-center justify-between gap-4 text-sm text-muted-foreground">
              <span className="ml-5">P90:</span>
              <span>{formatTokens(p90.value || 0)}</span>
            </div>
          )}
          {percentage && (
            <div className="flex items-center justify-between gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-purple-500" />
                <span>% of Supply:</span>
              </div>
              <span className="font-medium">{formatPercentage(percentage.value || 0)}</span>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Regular tooltip (no MC)
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
  // Check if Monte Carlo confidence bands are present
  const hasConfidenceBands = data.length > 0 &&
    data[0].expected_circulating_total_p10 !== undefined &&
    data[0].expected_circulating_total_p90 !== undefined

  // Debug logging
  console.log('CirculatingSupplyChart data[0]:', data[0])
  console.log('hasConfidenceBands:', hasConfidenceBands)

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Expected Circulating Supply Over Time
          {hasConfidenceBands && ' (with 80% confidence bands)'}
        </CardTitle>
        <CardDescription>
          {hasConfidenceBands
            ? 'Median circulating supply with P10-P90 confidence interval from Monte Carlo simulation'
            : 'Cumulative tokens expected to be circulating (unlocked - relocked)'}
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

            {hasConfidenceBands ? (
              <>
                {/* P10-P90 confidence band */}
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="expected_circulating_total_p90"
                  fill="#3b82f6"
                  fillOpacity={0.2}
                  stroke="none"
                  name="P90 (upper)"
                />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="expected_circulating_total_p10"
                  fill="#ffffff"
                  fillOpacity={1}
                  stroke="none"
                  name="P10 (lower)"
                />

                {/* Median line */}
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="expected_circulating_total_median"
                  stroke="#3b82f6"
                  strokeWidth={2.5}
                  name="Median Circulating"
                  dot={false}
                />

                {/* P10 and P90 boundary lines */}
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="expected_circulating_total_p10"
                  stroke="#3b82f6"
                  strokeWidth={1}
                  strokeDasharray="3 3"
                  strokeOpacity={0.5}
                  name="P10"
                  dot={false}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="expected_circulating_total_p90"
                  stroke="#3b82f6"
                  strokeWidth={1}
                  strokeDasharray="3 3"
                  strokeOpacity={0.5}
                  name="P90"
                  dot={false}
                />
              </>
            ) : (
              <>
                {/* Regular deterministic view */}
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
              </>
            )}

            {/* Percentage line - always shown */}
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
