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

  // Monte Carlo confidence bands (optional, only when Monte Carlo enabled)
  total_unlocked_p10?: number
  total_unlocked_p90?: number
  total_unlocked_median?: number
  total_unlocked_std?: number

  total_expected_sell_p10?: number
  total_expected_sell_p90?: number
  total_expected_sell_median?: number
  total_expected_sell_std?: number

  expected_circulating_total_p10?: number
  expected_circulating_total_p90?: number
  expected_circulating_total_median?: number
  expected_circulating_total_std?: number
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
