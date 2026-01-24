import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  TooltipProps
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { GlobalMetric } from '@/types/simulation'
import { formatTokens } from '@/lib/utils'

interface SellPressureChartProps {
  data: GlobalMetric[]
}

const CustomTooltip = ({ active, payload, label }: TooltipProps<number, string>) => {
  if (!active || !payload || !payload.length) return null

  const sellValue = payload[0]?.value || 0
  const volumeRatio = payload[0]?.payload?.sell_volume_ratio

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
  return (
    <Card>
      <CardHeader>
        <CardTitle>Expected Monthly Sell Pressure</CardTitle>
        <CardDescription>
          Estimated tokens sold to market each month based on behavior assumptions
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
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
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
