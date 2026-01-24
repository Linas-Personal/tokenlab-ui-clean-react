import {
  LineChart,
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

interface PriceEvolutionChartProps {
  data: GlobalMetric[]
}

const CustomTooltip = ({ active, payload, label }: TooltipProps<number, string>) => {
  if (!active || !payload || !payload.length) return null

  const price = payload[0]?.value || 0
  const initialPrice = 1.0
  const percentChange = ((price - initialPrice) / initialPrice) * 100

  return (
    <div className="bg-background border rounded-lg shadow-lg p-3">
      <p className="font-semibold mb-2">Month {label}</p>
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-4 text-sm">
          <span>Price:</span>
          <span className="font-medium">${price.toFixed(4)}</span>
        </div>
        <div className="flex items-center justify-between gap-4 text-sm">
          <span>Change from TGE:</span>
          <span
            className={`font-medium ${
              percentChange >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {percentChange >= 0 ? '+' : ''}
            {percentChange.toFixed(2)}%
          </span>
        </div>
      </div>
    </div>
  )
}

export function PriceEvolutionChart({ data }: PriceEvolutionChartProps) {
  const priceData = data.filter(d => d.current_price !== null && d.current_price !== undefined)

  if (priceData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Price Evolution</CardTitle>
          <CardDescription>Available in Tier 2/3 simulations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[400px] flex items-center justify-center text-muted-foreground">
            No price data available (Tier 1 mode)
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Price Evolution</CardTitle>
        <CardDescription>
          Token price over time based on dynamic pricing model (Tier 2/3)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={priceData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="month_index"
              label={{ value: 'Month', position: 'insideBottom', offset: -5 }}
              className="text-xs"
            />
            <YAxis
              label={{ value: 'Price (USD)', angle: -90, position: 'insideLeft' }}
              tickFormatter={(value) => `$${value.toFixed(2)}`}
              className="text-xs"
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="current_price"
              stroke="#10b981"
              strokeWidth={2.5}
              name="Token Price"
              dot={{ r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
