export interface TokenConfig {
  name: string
  total_supply: number
  start_date: string
  horizon_months: number
  allocation_mode: "percent" | "tokens"
  simulation_mode: "tier1" | "tier2" | "tier3"
}

export interface AssumptionsConfig {
  sell_pressure_level: "low" | "medium" | "high"
  avg_daily_volume_tokens: number | null
}

export interface CliffShockBehavior {
  enabled: boolean
  multiplier: number
  buckets: string[]
}

export interface PriceTriggerBehavior {
  enabled: boolean
  source: "flat" | "scenario" | "csv"
  scenario: "uptrend" | "downtrend" | "volatile" | null
  take_profit: number
  stop_loss: number
  extra_sell_addon: number
  uploaded_price_series: [number, number][] | null
}

export interface RelockBehavior {
  enabled: boolean
  relock_pct: number
  lock_duration_months: number
}

export interface BehaviorsConfig {
  cliff_shock: CliffShockBehavior
  price_trigger: PriceTriggerBehavior
  relock: RelockBehavior
}

export interface BucketConfig {
  bucket: string
  allocation: number
  tge_unlock_pct: number
  cliff_months: number
  vesting_months: number
  unlock_type: "linear"
}

export interface StakingTier2Config {
  enabled: boolean
  apy: number
  max_capacity_pct: number
  lockup_months: number
  participation_rate: number
  reward_source: "treasury" | "emission"
}

export interface PricingTier2Config {
  enabled: boolean
  pricing_model: "bonding_curve" | "linear" | "constant"
  initial_price: number
  target_price: number | null
  bonding_curve_param: number
}

export interface TreasuryTier2Config {
  enabled: boolean
  initial_balance_pct: number
  hold_pct: number
  liquidity_pct: number
  buyback_pct: number
}

export interface VolumeTier2Config {
  enabled: boolean
  volume_model: "proportional" | "constant"
  base_daily_volume: number
  volume_multiplier: number
}

export interface CohortBehaviorProfile {
  sell_pressure_mean: number
  sell_pressure_std: number
  stake_probability: number
  hold_probability: number
}

export interface CohortBehaviorTier3Config {
  enabled: boolean
  profiles: Record<string, CohortBehaviorProfile>
  bucket_cohort_mapping: Record<string, string>
}

export interface MonteCarloTier3Config {
  enabled: boolean
  num_trials: number
  variance_level: "low" | "medium" | "high"
  seed: number | null
}

export interface Tier2Config {
  staking: StakingTier2Config
  pricing: PricingTier2Config
  treasury: TreasuryTier2Config
  volume: VolumeTier2Config
}

export interface Tier3Config {
  cohort_behavior: CohortBehaviorTier3Config
  monte_carlo: MonteCarloTier3Config
}

export interface SimulationConfig {
  token: TokenConfig
  assumptions: AssumptionsConfig
  behaviors: BehaviorsConfig
  buckets: BucketConfig[]
  tier2?: Tier2Config
  tier3?: Tier3Config
  abm?: any
  monte_carlo?: any
}
