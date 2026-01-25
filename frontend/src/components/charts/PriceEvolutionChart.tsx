import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Area
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { GlobalMetric } from '@/types/simulation'

interface PriceEvolutionChartProps {
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
  // Note: Price confidence bands (current_price_p10/p90) are not currently implemented in backend
  // but this code is future-proof if they are added
  const hasMC = dataPoint?.current_price_p10 !== undefined || dataPoint?.current_price_p90 !== undefined

  if (hasMC) {
    const p10 = dataPoint?.current_price_p10
    const median = dataPoint?.current_price_median
    const p90 = dataPoint?.current_price_p90
    const initialPrice = 1.0

    return (
      <div className="bg-background border rounded-lg shadow-lg p-3">
        <p className="font-semibold mb-2">Month {label}</p>
        <div className="space-y-1">
          {median !== undefined && (
            <>
              <div className="flex items-center justify-between gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-green-500" />
                  <span>Median:</span>
                </div>
                <span className="font-medium">${median.toFixed(4)}</span>
              </div>
              <div className="flex items-center justify-between gap-4 text-sm text-muted-foreground">
                <span className="ml-5">Change:</span>
                <span className={median >= initialPrice ? 'text-green-600' : 'text-red-600'}>
                  {median >= initialPrice ? '+' : ''}
                  {(((median - initialPrice) / initialPrice) * 100).toFixed(2)}%
                </span>
              </div>
            </>
          )}
          {p10 !== undefined && (
            <div className="flex items-center justify-between gap-4 text-sm text-muted-foreground">
              <span className="ml-5">P10:</span>
              <span>${p10.toFixed(4)}</span>
            </div>
          )}
          {p90 !== undefined && (
            <div className="flex items-center justify-between gap-4 text-sm text-muted-foreground">
              <span className="ml-5">P90:</span>
              <span>${p90.toFixed(4)}</span>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Regular tooltip (no MC)
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

  // Note: Price confidence bands are not currently implemented in backend
  // This code is future-proof if current_price_p10/p90 are added later
  const hasConfidenceBands = priceData.length > 0 &&
    (priceData[0] as any).current_price_p10 !== undefined &&
    (priceData[0] as any).current_price_p90 !== undefined

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
        <CardTitle>
          Price Evolution
          {hasConfidenceBands && ' (with 80% confidence bands)'}
        </CardTitle>
        <CardDescription>
          {hasConfidenceBands
            ? 'Median price with P10-P90 confidence interval from Monte Carlo simulation'
            : 'Token price over time based on dynamic pricing model (Tier 2/3)'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          {hasConfidenceBands ? (
            <ComposedChart data={priceData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
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

              {/* P10-P90 confidence band */}
              <Area
                type="monotone"
                dataKey="current_price_p90"
                fill="#10b981"
                fillOpacity={0.2}
                stroke="none"
                name="P90 (upper)"
              />
              <Area
                type="monotone"
                dataKey="current_price_p10"
                fill="#ffffff"
                fillOpacity={1}
                stroke="none"
                name="P10 (lower)"
              />

              {/* Median line */}
              <Line
                type="monotone"
                dataKey="current_price_median"
                stroke="#10b981"
                strokeWidth={2.5}
                name="Median Price"
                dot={{ r: 3 }}
              />

              {/* P10 and P90 boundary lines */}
              <Line
                type="monotone"
                dataKey="current_price_p10"
                stroke="#10b981"
                strokeWidth={1}
                strokeDasharray="3 3"
                strokeOpacity={0.5}
                name="P10"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="current_price_p90"
                stroke="#10b981"
                strokeWidth={1}
                strokeDasharray="3 3"
                strokeOpacity={0.5}
                name="P90"
                dot={false}
              />
            </ComposedChart>
          ) : (
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
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
