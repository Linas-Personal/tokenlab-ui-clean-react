import type { SimulationConfig, BucketConfig } from '@/types/config'

export const DEFAULT_BUCKETS: BucketConfig[] = [
  {
    bucket: "Team",
    allocation: 20,
    tge_unlock_pct: 0,
    cliff_months: 12,
    vesting_months: 36,
    unlock_type: "linear"
  },
  {
    bucket: "Seed",
    allocation: 10,
    tge_unlock_pct: 10,
    cliff_months: 6,
    vesting_months: 18,
    unlock_type: "linear"
  },
  {
    bucket: "Private",
    allocation: 15,
    tge_unlock_pct: 15,
    cliff_months: 3,
    vesting_months: 12,
    unlock_type: "linear"
  },
  {
    bucket: "Treasury",
    allocation: 30,
    tge_unlock_pct: 0,
    cliff_months: 0,
    vesting_months: 48,
    unlock_type: "linear"
  },
  {
    bucket: "Liquidity",
    allocation: 25,
    tge_unlock_pct: 100,
    cliff_months: 0,
    vesting_months: 0,
    unlock_type: "linear"
  }
]

export const DEFAULT_CONFIG: SimulationConfig = {
  token: {
    name: "My Token",
    total_supply: 1000000000,
    start_date: new Date().toISOString().split('T')[0],
    horizon_months: 36,
    allocation_mode: "percent",
    simulation_mode: "tier1"
  },
  assumptions: {
    sell_pressure_level: "medium",
    avg_daily_volume_tokens: null
  },
  behaviors: {
    cliff_shock: {
      enabled: false,
      multiplier: 3.0,
      buckets: []
    },
    price_trigger: {
      enabled: false,
      source: "flat",
      scenario: null,
      take_profit: 0.5,
      stop_loss: -0.3,
      extra_sell_addon: 0.2,
      uploaded_price_series: null
    },
    relock: {
      enabled: false,
      relock_pct: 0.3,
      lock_duration_months: 6
    }
  },
  buckets: DEFAULT_BUCKETS,
  tier2: {
    staking: {
      enabled: false,
      apy: 0.12,
      max_capacity_pct: 0.5,
      lockup_months: 6,
      participation_rate: 0.3,
      reward_source: "treasury"
    },
    pricing: {
      enabled: false,
      pricing_model: "bonding_curve",
      initial_price: 1.0,
      target_price: null,
      bonding_curve_param: 2.0
    },
    treasury: {
      enabled: false,
      initial_balance_pct: 0.15,
      hold_pct: 0.5,
      liquidity_pct: 0.3,
      buyback_pct: 0.2
    },
    volume: {
      enabled: false,
      volume_model: "proportional",
      base_daily_volume: 10000000,
      volume_multiplier: 1.0
    }
  },
  tier3: {
    cohort_behavior: {
      enabled: false,
      profiles: {
        high_stake: {
          sell_pressure_mean: 0.1,
          sell_pressure_std: 0.03,
          stake_probability: 0.7,
          hold_probability: 0.2
        },
        high_sell: {
          sell_pressure_mean: 0.6,
          sell_pressure_std: 0.1,
          stake_probability: 0.05,
          hold_probability: 0.05
        },
        balanced: {
          sell_pressure_mean: 0.25,
          sell_pressure_std: 0.05,
          stake_probability: 0.3,
          hold_probability: 0.5
        }
      },
      bucket_cohort_mapping: {}
    },
    monte_carlo: {
      enabled: false,
      num_trials: 100,
      variance_level: "medium",
      seed: null
    }
  },
  abm: {
    agent_granularity: "adaptive",
    agents_per_cohort: 50,
    pricing_model: "eoe",
    pricing_config: {
      holding_time: 3.0,
      smoothing_factor: 0.7,
      min_price: 0.01,
      k: 0.000001,
      n: 2.0,
      initial_price: 1.0,
      alpha: 1.0
    },
    enable_staking: false,
    staking_config: {
      base_apy: 0.15,
      max_capacity_pct: 0.40,
      lockup_months: 6,
      reward_source: "emission",
      apy_multiplier_at_empty: 1.5,
      apy_multiplier_at_full: 0.5
    },
    enable_treasury: false,
    treasury_config: {
      initial_balance_pct: 0.15,
      transaction_fee_pct: 0.02,
      hold_pct: 0.50,
      liquidity_pct: 0.30,
      buyback_pct: 0.20,
      burn_bought_tokens: true
    },
    enable_volume: false,
    volume_config: {
      volume_model: "proportional",
      base_daily_volume: 10000000,
      volume_multiplier: 1.0
    },
    bucket_cohort_mapping: {},
    initial_price: 1.0,
    seed: null,
    store_cohort_details: true
  },
  monte_carlo: {
    enabled: false,
    num_trials: 100,
    variance_level: "medium",
    seed: null,
    confidence_levels: [10, 50, 90]
  }
}

export const SELL_PRESSURE_LEVELS = {
  low: { value: "low" as const, label: "Low (10%)" },
  medium: { value: "medium" as const, label: "Medium (25%)" },
  high: { value: "high" as const, label: "High (50%)" }
}

export const PRICE_SCENARIOS = {
  uptrend: { value: "uptrend" as const, label: "Uptrend (+5%/month)" },
  downtrend: { value: "downtrend" as const, label: "Downtrend (-5%/month)" },
  volatile: { value: "volatile" as const, label: "Volatile (±10%)" }
}
