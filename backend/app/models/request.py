"""
Pydantic request models for API validation.
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Literal, Tuple
from datetime import datetime


class TokenConfig(BaseModel):
    """Token configuration."""
    name: str = Field(..., min_length=1, max_length=100)
    total_supply: int = Field(..., ge=0)  # Allow 0 for edge case testing
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    horizon_months: int = Field(..., ge=0, le=240)  # Allow 0 for TGE-only scenarios
    allocation_mode: Literal["percent", "tokens"] = "percent"
    simulation_mode: Literal["tier1", "tier2", "tier3"] = "tier1"

    @field_validator("start_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        datetime.strptime(v, "%Y-%m-%d")
        return v


class AssumptionsConfig(BaseModel):
    """Market assumptions configuration."""
    sell_pressure_level: Literal["low", "medium", "high"] = "medium"
    avg_daily_volume_tokens: Optional[float] = Field(None, ge=0)


class CliffShockBehavior(BaseModel):
    """Cliff shock behavior configuration."""
    enabled: bool = False
    multiplier: float = Field(3.0, ge=1.0, le=10.0)
    buckets: List[str] = Field(default_factory=list)


class PriceTriggerBehavior(BaseModel):
    """Price trigger behavior configuration."""
    enabled: bool = False
    source: Literal["flat", "scenario", "csv"] = "flat"
    scenario: Optional[Literal["uptrend", "downtrend", "volatile"]] = None
    take_profit: float = Field(0.5, ge=-1.0, le=10.0)
    stop_loss: float = Field(-0.3, ge=-1.0, le=1.0)
    extra_sell_addon: float = Field(0.2, ge=0.0, le=1.0)
    uploaded_price_series: Optional[List[Tuple[int, float]]] = None


class RelockBehavior(BaseModel):
    """Relock/staking delay behavior configuration."""
    enabled: bool = False
    relock_pct: float = Field(0.3, ge=0.0, le=1.0)
    lock_duration_months: int = Field(6, ge=0, le=120)


class BehaviorsConfig(BaseModel):
    """Behavioral modifiers configuration."""
    cliff_shock: CliffShockBehavior = Field(default_factory=CliffShockBehavior)
    price_trigger: PriceTriggerBehavior = Field(default_factory=PriceTriggerBehavior)
    relock: RelockBehavior = Field(default_factory=RelockBehavior)


class BucketConfig(BaseModel):
    """Vesting bucket configuration."""
    bucket: str = Field(..., min_length=1)
    allocation: float = Field(..., ge=0)
    tge_unlock_pct: float = Field(..., ge=0, le=100)
    cliff_months: int = Field(..., ge=0)
    vesting_months: int = Field(..., ge=0)
    unlock_type: Literal["linear"] = "linear"


class StakingTier2Config(BaseModel):
    """Dynamic staking configuration for Tier 2."""
    enabled: bool = False
    apy: float = Field(0.12, ge=0, le=10.0)
    max_capacity_pct: float = Field(0.5, ge=0, le=1.0)
    lockup_months: int = Field(6, ge=0, le=60)
    participation_rate: float = Field(0.3, ge=0, le=1.0)
    reward_source: Literal["treasury", "emission"] = "treasury"


class PricingTier2Config(BaseModel):
    """Dynamic pricing configuration for Tier 2."""
    enabled: bool = False
    pricing_model: Literal["bonding_curve", "linear", "constant"] = "bonding_curve"
    initial_price: float = Field(1.0, gt=0)
    target_price: Optional[float] = Field(None, gt=0)
    bonding_curve_param: float = Field(2.0, ge=0.1, le=10.0)


class TreasuryTier2Config(BaseModel):
    """Treasury strategy configuration for Tier 2."""
    enabled: bool = False
    initial_balance_pct: float = Field(0.15, ge=0, le=1.0)
    hold_pct: float = Field(0.5, ge=0, le=1.0)
    liquidity_pct: float = Field(0.3, ge=0, le=1.0)
    buyback_pct: float = Field(0.2, ge=0, le=1.0)

    @model_validator(mode='after')
    def validate_percentages_sum(self):
        total = self.hold_pct + self.liquidity_pct + self.buyback_pct
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Treasury percentages must sum to 1.0, got {total}")
        return self


class VolumeTier2Config(BaseModel):
    """Dynamic volume configuration for Tier 2."""
    enabled: bool = False
    volume_model: Literal["proportional", "constant"] = "proportional"
    base_daily_volume: float = Field(10000000, gt=0)
    volume_multiplier: float = Field(1.0, ge=0.1, le=100.0)


class CohortBehaviorProfile(BaseModel):
    """Cohort behavior profile for Tier 3."""
    sell_pressure_mean: float = Field(0.25, ge=0, le=1.0)
    sell_pressure_std: float = Field(0.05, ge=0, le=0.5)
    stake_probability: float = Field(0.3, ge=0, le=1.0)
    hold_probability: float = Field(0.5, ge=0, le=1.0)


class CohortBehaviorTier3Config(BaseModel):
    """Cohort-based behavior configuration for Tier 3."""
    enabled: bool = False
    profiles: dict[str, CohortBehaviorProfile] = Field(
        default_factory=lambda: {
            "high_stake": CohortBehaviorProfile(
                sell_pressure_mean=0.1,
                sell_pressure_std=0.03,
                stake_probability=0.7,
                hold_probability=0.2
            ),
            "high_sell": CohortBehaviorProfile(
                sell_pressure_mean=0.6,
                sell_pressure_std=0.1,
                stake_probability=0.05,
                hold_probability=0.05
            ),
            "balanced": CohortBehaviorProfile(
                sell_pressure_mean=0.25,
                sell_pressure_std=0.05,
                stake_probability=0.3,
                hold_probability=0.5
            ),
        }
    )
    bucket_cohort_mapping: dict[str, str] = Field(default_factory=dict)


class MonteCarloTier3Config(BaseModel):
    """Monte Carlo simulation configuration for Tier 3."""
    enabled: bool = False
    num_trials: int = Field(100, ge=10, le=10000)
    variance_level: Literal["low", "medium", "high"] = "medium"
    seed: Optional[int] = Field(None, ge=0)


class Tier2Config(BaseModel):
    """Tier 2 advanced configuration."""
    staking: StakingTier2Config = Field(default_factory=StakingTier2Config)
    pricing: PricingTier2Config = Field(default_factory=PricingTier2Config)
    treasury: TreasuryTier2Config = Field(default_factory=TreasuryTier2Config)
    volume: VolumeTier2Config = Field(default_factory=VolumeTier2Config)


class Tier3Config(BaseModel):
    """Tier 3 advanced configuration."""
    cohort_behavior: CohortBehaviorTier3Config = Field(default_factory=CohortBehaviorTier3Config)
    monte_carlo: MonteCarloTier3Config = Field(default_factory=MonteCarloTier3Config)


class SimulationConfig(BaseModel):
    """Complete simulation configuration."""
    token: TokenConfig
    assumptions: AssumptionsConfig = Field(default_factory=AssumptionsConfig)
    behaviors: BehaviorsConfig = Field(default_factory=BehaviorsConfig)
    buckets: List[BucketConfig] = Field(..., min_length=1)
    tier2: Optional[Tier2Config] = None
    tier3: Optional[Tier3Config] = None

    @model_validator(mode='after')
    def validate_allocation_sum(self):
        """Validate total allocation doesn't exceed limits."""
        allocation_mode = self.token.allocation_mode
        total = sum(b.allocation for b in self.buckets)

        if allocation_mode == "percent":
            if total > 100.01:
                raise ValueError(f"Allocation sum ({total}%) exceeds 100%")
        else:
            if total > self.token.total_supply:
                raise ValueError(
                    f"Allocation sum ({total:,.0f}) exceeds total supply ({self.token.total_supply:,.0f})"
                )

        return self

    @model_validator(mode='after')
    def validate_tier_config(self):
        """Validate tier-specific configuration is present when needed."""
        mode = self.token.simulation_mode

        if mode in ["tier2", "tier3"] and self.tier2 is None:
            self.tier2 = Tier2Config()

        if mode == "tier3" and self.tier3 is None:
            self.tier3 = Tier3Config()

        return self


class SimulateRequest(BaseModel):
    """Request model for simulation endpoint."""
    config: SimulationConfig


class ValidateConfigRequest(BaseModel):
    """Request model for config validation endpoint."""
    config: dict
