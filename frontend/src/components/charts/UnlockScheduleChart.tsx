import { useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { BucketResult } from '@/types/simulation'
import { formatTokens } from '@/lib/utils'

interface UnlockScheduleChartProps {
  data: BucketResult[]
}

const CHART_COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
]

interface ChartDataPoint {
  month: number
  [bucket: string]: number
}

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{
    name: string
    value: number
    color: string
  }>
  label?: string | number
}

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (!active || !payload || !payload.length) return null

  return (
    <div className="bg-background border rounded-lg shadow-lg p-3">
      <p className="font-semibold mb-2">Month {label}</p>
      <div className="space-y-1">
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: entry.color }}
              />
              <span>{entry.name}:</span>
            </div>
            <span className="font-medium">{formatTokens(entry.value || 0)}</span>
          </div>
        ))}
      </div>
      <div className="mt-2 pt-2 border-t">
        <div className="flex justify-between gap-4 text-sm font-semibold">
          <span>Total:</span>
          <span>
            {formatTokens(
              payload.reduce((sum, entry) => sum + (entry.value || 0), 0)
            )}
          </span>
        </div>
      </div>
    </div>
  )
}

export function UnlockScheduleChart({ data }: UnlockScheduleChartProps) {
  const { chartData, buckets } = useMemo(() => {
    const monthsSet = new Set(data.map(d => d.month_index))
    const months = Array.from(monthsSet).sort((a, b) => a - b)
    const bucketsSet = new Set(data.map(d => d.bucket))
    const bucketsList = Array.from(bucketsSet)

    const chartDataPoints: ChartDataPoint[] = months.map(month => {
      const point: ChartDataPoint = { month }

      data
        .filter(d => d.month_index === month)
        .forEach(d => {
          point[d.bucket] = d.unlocked_this_month
        })

      return point
    })

    return {
      chartData: chartDataPoints,
      buckets: bucketsList
    }
  }, [data])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Monthly Unlock Schedule by Bucket</CardTitle>
        <CardDescription>
          Tokens unlocking each month across all vesting buckets
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="month"
              label={{ value: 'Month', position: 'insideBottom', offset: -5 }}
              className="text-xs"
            />
            <YAxis
              label={{ value: 'Tokens Unlocked', angle: -90, position: 'insideLeft' }}
              tickFormatter={(value) => formatTokens(value)}
              className="text-xs"
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            {buckets.map((bucket, index) => (
              <Bar
                key={bucket}
                dataKey={bucket}
                stackId="a"
                fill={CHART_COLORS[index % CHART_COLORS.length]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
