/**
 * TypeScript types for ABM (Agent-Based Model) API
 *
 * These types mirror the backend Pydantic models exactly.
 */

// ===========================
// Enums
// ===========================

export const JobStatus = {
  PENDING: "pending",
  RUNNING: "running",
  COMPLETED: "completed",
  FAILED: "failed",
  CANCELLED: "cancelled"
} as const;

export type JobStatus = typeof JobStatus[keyof typeof JobStatus];

export const AgentGranularity = {
  FULL_INDIVIDUAL: "full_individual",
  ADAPTIVE: "adaptive",
  META_AGENTS: "meta_agents"
} as const;

export type AgentGranularity = typeof AgentGranularity[keyof typeof AgentGranularity];

export const PricingModelEnum = {
  EOE: "eoe",
  BONDING_CURVE: "bonding_curve",
  ISSUANCE_CURVE: "issuance_curve",
  CONSTANT: "constant"
} as const;

export type PricingModelEnum = typeof PricingModelEnum[keyof typeof PricingModelEnum];

export const RewardSource = {
  EMISSION: "emission",
  TREASURY: "treasury"
} as const;

export type RewardSource = typeof RewardSource[keyof typeof RewardSource];

export const ScalingStrategy = {
  FULL_INDIVIDUAL: "full_individual",
  REPRESENTATIVE_SAMPLING: "representative_sampling",
  META_AGENTS: "meta_agents"
} as const;

export type ScalingStrategy = typeof ScalingStrategy[keyof typeof ScalingStrategy];

// ===========================
// Configuration Types
// ===========================

export interface StakingConfig {
  base_apy: number;
  max_capacity_pct: number;
  lockup_months: number;
  reward_source: RewardSource;
  apy_multiplier_at_empty?: number;
  apy_multiplier_at_full?: number;
}

export interface TreasuryConfig {
  initial_balance_pct: number;
  transaction_fee_pct: number;
  hold_pct: number;
  liquidity_pct: number;
  buyback_pct: number;
  burn_bought_tokens: boolean;
}

export interface EOEPricingConfig {
  holding_time: number;
  smoothing_factor: number;
  min_price: number;
}

export interface BondingCurvePricingConfig {
  k: number;
  n: number;
}

export interface IssuanceCurvePricingConfig {
  initial_price: number;
  alpha: number;
}

export type PricingConfig = EOEPricingConfig | BondingCurvePricingConfig | IssuanceCurvePricingConfig | Record<string, never>;

export interface CohortProfile {
  risk_alpha: number;
  risk_beta: number;
  hold_time_shape: number;
  hold_time_scale: number;
  sell_pressure_mean: number;
  sell_pressure_std: number;
  stake_alpha: number;
  stake_beta: number;
  cliff_shock_mult: number;
  price_sensitivity_mean: number;
  price_sensitivity_std: number;
  take_profit_mean: number;
  take_profit_std: number;
  stop_loss_mean: number;
  stop_loss_std: number;
}

export interface ABMConfig {
  agent_granularity: AgentGranularity;
  agents_per_cohort?: number;
  pricing_model: PricingModelEnum;
  pricing_config?: PricingConfig;
  enable_staking: boolean;
  staking_config?: StakingConfig;
  enable_treasury: boolean;
  treasury_config?: TreasuryConfig;
  initial_price?: number;
  cohort_profiles?: Record<string, CohortProfile>;
  seed?: number;
  store_cohort_details?: boolean;
}

export interface MonteCarloConfig {
  num_trials: number;
  seed?: number;
  confidence_levels?: number[];
  parallel_execution?: boolean;
  max_workers?: number;
}

// ===========================
// Request Types
// ===========================

export interface ABMSimulationRequest {
  token: {
    name: string;
    total_supply: number;
    start_date: string;
    horizon_months: number;
  };
  buckets: Array<{
    bucket: string;
    allocation: number;
    tge_unlock_pct: number;
    cliff_months: number;
    vesting_months: number;
  }>;
  abm: ABMConfig;
  monte_carlo?: MonteCarloConfig;
}

// ===========================
// Response Types - Job Management
// ===========================

export interface JobSubmissionResponse {
  job_id: string;
  status: JobStatus;
  status_url: string;
  stream_url: string;
  results_url: string;
  cached: boolean;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress_pct: number;
  current_month?: number;
  total_months?: number;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface JobListResponse {
  jobs: Array<{
    job_id: string;
    status: JobStatus;
    progress_pct: number;
    created_at: string;
  }>;
}

export interface QueueStatsResponse {
  total_jobs: number;
  pending_jobs: number;
  running_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  cache_size: number;
  cache_hits: number;
  cache_misses: number;
}

// ===========================
// Response Types - SSE Progress
// ===========================

export interface SSEProgressMessage {
  type: "progress" | "done" | "error";
  job_id: string;
  status: JobStatus;
  progress_pct: number;
  current_month?: number;
  total_months?: number;
  error_message?: string;
}

// ===========================
// Response Types - Simulation Results
// ===========================

export interface ABMGlobalMetric {
  month_index: number;
  date: string;
  price: number;
  circulating_supply: number;
  total_unlocked: number;
  total_sold: number;
  total_staked: number;
  total_held: number;
}

export interface ABMCohortMetric {
  month_index: number;
  cohort: string;
  num_agents: number;
  total_locked: number;
  total_unlocked: number;
  total_staked: number;
  total_sold: number;
  total_held: number;
  avg_price_sensitivity?: number;
  avg_risk_tolerance?: number;
}

export interface StakingMetrics {
  total_staked: number;
  current_apy: number;
  utilization_pct: number;
  total_rewards_paid: number;
  num_stakers: number;
}

export interface TreasuryMetrics {
  fiat_balance: number;
  token_balance: number;
  total_fees_collected_fiat: number;
  total_tokens_bought: number;
  total_tokens_burned: number;
  total_liquidity_deployed: number;
}

export interface ABMSummaryCards {
  final_price: number;
  final_circulating_supply: number;
  total_sold_cumulative: number;
  total_staked_cumulative: number;
  avg_monthly_sell_pressure: number;
  max_monthly_sell_pressure: number;
  price_change_pct: number;
  num_agents: number;
  num_cohorts: number;
  total_months: number;
  staking_metrics?: StakingMetrics;
  treasury_metrics?: TreasuryMetrics;
}

export interface ABMSimulationResults {
  global_metrics: ABMGlobalMetric[];
  cohort_metrics?: ABMCohortMetric[];
  summary: ABMSummaryCards;
  execution_time_seconds: number;
  warnings: string[];
  config: {
    num_agents: number;
    pricing_model: string;
    has_staking: boolean;
    has_treasury: boolean;
    start_date: string;
  };
}

// ===========================
// Monte Carlo Types
// ===========================

export interface MonteCarloTrial {
  trial_index: number;
  global_metrics: ABMGlobalMetric[];
  final_price: number;
  total_sold: number;
  seed: number;
}

export interface MonteCarloPercentile {
  percentile: number;
  global_metrics: ABMGlobalMetric[];
  final_price: number;
  total_sold: number;
}

export interface MonteCarloResults {
  trials: MonteCarloTrial[];
  percentiles: MonteCarloPercentile[];
  mean_metrics: ABMGlobalMetric[];
  summary: {
    num_trials: number;
    mean_final_price: number;
    std_final_price: number;
    min_final_price: number;
    max_final_price: number;
    p10_final_price: number;
    p50_final_price: number;
    p90_final_price: number;
  };
  execution_time_seconds: number;
}

// ===========================
// Error Types
// ===========================

export interface ABMErrorResponse {
  detail: string;
  job_id?: string;
  error_type?: string;
}

// ===========================
// Utility Types
// ===========================

export interface ScalingStrategyInfo {
  strategy: ScalingStrategy;
  estimated_agents: number;
  time_per_iteration_sec: number;
  total_time_sec: number;
  memory_mb: number;
  holders_per_agent: number;
}

// ===========================
// Helper Type Guards
// ===========================

export function isJobCompleted(status: JobStatus): boolean {
  return status === JobStatus.COMPLETED;
}

export function isJobFailed(status: JobStatus): boolean {
  return status === JobStatus.FAILED;
}

export function isJobRunning(status: JobStatus): boolean {
  return status === JobStatus.RUNNING;
}

export function isJobPending(status: JobStatus): boolean {
  return status === JobStatus.PENDING;
}

export function isJobFinished(status: JobStatus): boolean {
  return status === JobStatus.COMPLETED || status === JobStatus.FAILED || status === JobStatus.CANCELLED;
}

export function hasStakingMetrics(summary: ABMSummaryCards): summary is ABMSummaryCards & { staking_metrics: StakingMetrics } {
  return summary.staking_metrics !== undefined;
}

export function hasTreasuryMetrics(summary: ABMSummaryCards): summary is ABMSummaryCards & { treasury_metrics: TreasuryMetrics } {
  return summary.treasury_metrics !== undefined;
}
