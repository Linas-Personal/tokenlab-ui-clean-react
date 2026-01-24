export interface BucketResult {
  month_index: number
  date: string
  bucket: string
  allocation_tokens: number
  unlocked_this_month: number
  unlocked_cumulative: number
  locked_remaining: number
  sell_pressure_effective: number
  expected_sell_this_month: number
  expected_circulating_cumulative: number
}

export interface GlobalMetric {
  month_index: number
  date: string
  total_unlocked: number
  total_expected_sell: number
  expected_circulating_total: number
  expected_circulating_pct: number
  sell_volume_ratio?: number
  current_price?: number
  staked_amount?: number
  liquidity_deployed?: number
  treasury_balance?: number
}

export interface SummaryCards {
  max_unlock_tokens: number
  max_unlock_month: number
  max_sell_tokens: number
  max_sell_month: number
  circ_12_pct: number
  circ_24_pct: number
  circ_end_pct: number
}

export interface SimulationData {
  bucket_results: BucketResult[]
  global_metrics: GlobalMetric[]
  summary_cards: SummaryCards
}

export interface SimulationResponse {
  status: string
  execution_time_ms: number
  warnings: string[]
  data: SimulationData
}
