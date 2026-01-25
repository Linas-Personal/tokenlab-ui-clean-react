import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  Legend
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { GlobalMetric } from '@/types/simulation'
import { formatTokens } from '@/lib/utils'

interface SellPressureChartProps {
  data: GlobalMetric[]
}

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{
    dataKey: string
    value: number
    payload?: any
    name: string
  }>
  label?: string | number
}

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (!active || !payload || !payload.length) return null

  const dataPoint = payload[0]?.payload
  const hasMC = dataPoint?.total_expected_sell_p10 !== undefined || dataPoint?.total_expected_sell_p90 !== undefined

  if (hasMC) {
    const p10 = dataPoint?.total_expected_sell_p10
    const median = dataPoint?.total_expected_sell_median
    const p90 = dataPoint?.total_expected_sell_p90
    const volumeRatio = dataPoint?.sell_volume_ratio

    return (
      <div className="bg-background border rounded-lg shadow-lg p-3">
        <p className="font-semibold mb-2">Month {label}</p>
        <div className="space-y-1">
          {median !== undefined && (
            <div className="flex items-center justify-between gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-red-500" />
                <span>Median:</span>
              </div>
              <span className="font-medium">{formatTokens(median)}</span>
            </div>
          )}
          {p10 !== undefined && (
            <div className="flex items-center justify-between gap-4 text-sm text-muted-foreground">
              <span className="ml-5">P10:</span>
              <span>{formatTokens(p10)}</span>
            </div>
          )}
          {p90 !== undefined && (
            <div className="flex items-center justify-between gap-4 text-sm text-muted-foreground">
              <span className="ml-5">P90:</span>
              <span>{formatTokens(p90)}</span>
            </div>
          )}
          {volumeRatio !== null && volumeRatio !== undefined && (
            <div className="flex items-center justify-between gap-4 text-sm">
              <span>Sell/Volume:</span>
              <span className="font-medium">{volumeRatio.toFixed(2)}x</span>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Regular tooltip (no MC)
  const sellValue = payload[0]?.value || 0
  const volumeRatio = dataPoint?.sell_volume_ratio

  return (
    <div className="bg-background border rounded-lg shadow-lg p-3">
      <p className="font-semibold mb-2">Month {label}</p>
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-4 text-sm">
          <span>Expected Sell:</span>
          <span className="font-medium">{formatTokens(sellValue)}</span>
        </div>
        {volumeRatio !== null && volumeRatio !== undefined && (
          <div className="flex items-center justify-between gap-4 text-sm">
            <span>Sell/Volume:</span>
            <span className="font-medium">{volumeRatio.toFixed(2)}x</span>
          </div>
        )}
      </div>
    </div>
  )
}

export function SellPressureChart({ data }: SellPressureChartProps) {
  // Check if Monte Carlo confidence bands are present
  const hasConfidenceBands = data.length > 0 &&
    data[0].total_expected_sell_p10 !== undefined &&
    data[0].total_expected_sell_p90 !== undefined

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Expected Monthly Sell Pressure
          {hasConfidenceBands && ' (with 80% confidence bands)'}
        </CardTitle>
        <CardDescription>
          {hasConfidenceBands
            ? 'Median sell pressure with P10-P90 confidence interval from Monte Carlo simulation'
            : 'Estimated tokens sold to market each month based on behavior assumptions'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          {hasConfidenceBands ? (
            <ComposedChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="month_index"
                label={{ value: 'Month', position: 'insideBottom', offset: -5 }}
                className="text-xs"
              />
              <YAxis
                label={{ value: 'Expected Sell Volume', angle: -90, position: 'insideLeft' }}
                tickFormatter={(value) => formatTokens(value)}
                className="text-xs"
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />

              {/* P10-P90 confidence band */}
              <Area
                type="monotone"
                dataKey="total_expected_sell_p90"
                fill="#ef4444"
                fillOpacity={0.2}
                stroke="none"
                name="P90 (upper)"
              />
              <Area
                type="monotone"
                dataKey="total_expected_sell_p10"
                fill="#ffffff"
                fillOpacity={1}
                stroke="none"
                name="P10 (lower)"
              />

              {/* Median line */}
              <Line
                type="monotone"
                dataKey="total_expected_sell_median"
                stroke="#ef4444"
                strokeWidth={2.5}
                name="Median Sell"
                dot={false}
              />

              {/* P10 and P90 boundary lines */}
              <Line
                type="monotone"
                dataKey="total_expected_sell_p10"
                stroke="#ef4444"
                strokeWidth={1}
                strokeDasharray="3 3"
                strokeOpacity={0.5}
                name="P10"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="total_expected_sell_p90"
                stroke="#ef4444"
                strokeWidth={1}
                strokeDasharray="3 3"
                strokeOpacity={0.5}
                name="P90"
                dot={false}
              />
            </ComposedChart>
          ) : (
            <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="month_index"
                label={{ value: 'Month', position: 'insideBottom', offset: -5 }}
                className="text-xs"
              />
              <YAxis
                label={{ value: 'Expected Sell Volume', angle: -90, position: 'insideLeft' }}
                tickFormatter={(value) => formatTokens(value)}
                className="text-xs"
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="total_expected_sell" fill="#ef4444" />
            </BarChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
