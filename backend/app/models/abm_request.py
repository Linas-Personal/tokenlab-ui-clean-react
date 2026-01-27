"""
Pydantic request models for ABM API.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from datetime import date


class TokenConfig(BaseModel):
    """Token configuration with required fields."""
    name: str = Field(..., min_length=1, description="Token name")
    total_supply: float = Field(..., gt=0, description="Total token supply")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD format)")
    horizon_months: int = Field(..., ge=1, le=240, description="Simulation horizon in months")
    initial_price: Optional[float] = Field(1.0, gt=0, description="Initial token price")
    simulation_mode: Optional[str] = Field("abm", description="Simulation mode")

    @field_validator('start_date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in YYYY-MM-DD format."""
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('start_date must be in YYYY-MM-DD format')


class BucketConfig(BaseModel):
    """Bucket (cohort) allocation configuration."""
    bucket: str = Field(..., min_length=1, description="Bucket/cohort name")
    allocation: float = Field(..., ge=0, le=100, description="Allocation percentage")
    tge_unlock_pct: float = Field(..., ge=0, le=100, description="TGE unlock percentage")
    cliff_months: int = Field(..., ge=0, description="Cliff period in months")
    vesting_months: int = Field(..., ge=0, description="Vesting period in months")
    num_holders: Optional[int] = Field(None, ge=1, description="Number of holders in this cohort")

    @field_validator('allocation', 'tge_unlock_pct')
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        """Ensure percentages are valid."""
        if v < 0 or v > 100:
            raise ValueError('Percentage must be between 0 and 100')
        return v


class AgentGranularity(str, Enum):
    """Agent creation strategy."""
    FULL_INDIVIDUAL = "full_individual"  # 1:1 mapping (slow, most accurate)
    ADAPTIVE = "adaptive"  # Adaptive based on total holders
    META_AGENTS = "meta_agents"  # Fixed number of meta-agents (fast)


class PricingModelEnum(str, Enum):
    """Available pricing models."""
    EOE = "eoe"
    BONDING_CURVE = "bonding_curve"
    ISSUANCE_CURVE = "issuance_curve"
    CONSTANT = "constant"


class AggregationLevel(str, Enum):
    """Result aggregation level."""
    COHORT = "cohort"  # Cohort-level only (small payload)
    SAMPLED = "sampled"  # Sample of agents (medium)
    FULL = "full"  # All agents (large!)


class ABMConfig(BaseModel):
    """ABM-specific configuration."""
    # Agent settings
    agent_granularity: AgentGranularity = AgentGranularity.ADAPTIVE
    agents_per_cohort: int = Field(50, ge=1, le=1000, description="Agents per cohort (for adaptive/meta modes)")

    # Pricing
    pricing_model: PricingModelEnum = PricingModelEnum.EOE
    pricing_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "initial_price": 1.0,
            "holding_time": 6.0,
            "smoothing_factor": 0.7
        }
    )

    # Dynamic systems (Phase 3)
    enable_staking: bool = False
    staking_config: Optional[Dict[str, Any]] = None

    enable_treasury: bool = False
    treasury_config: Optional[Dict[str, Any]] = None

    # Volume configuration
    enable_volume: bool = False
    volume_config: Optional[Dict[str, Any]] = None

    # Cohort behavior mapping (bucket name -> preset)
    bucket_cohort_mapping: Optional[Dict[str, str]] = Field(
        None,
        description="Map bucket names to cohort presets (conservative, moderate, aggressive)"
    )

    # Output settings
    store_cohort_details: bool = True
    aggregation_level: AggregationLevel = AggregationLevel.COHORT

    # Random seed for reproducibility
    seed: Optional[int] = None


class CohortProfileOverride(BaseModel):
    """Override default cohort profile parameters."""
    sell_pressure_mean: Optional[float] = Field(None, ge=0, le=1.0)
    sell_pressure_std: Optional[float] = Field(None, ge=0, le=0.5)
    stake_probability: Optional[float] = Field(None, ge=0, le=1.0)
    risk_tolerance_mean: Optional[float] = Field(None, ge=0, le=1.0)


class VolumeConfig(BaseModel):
    """Dynamic volume configuration."""
    volume_model: Literal["proportional", "constant"] = "proportional"
    base_daily_volume: float = Field(10_000_000, gt=0, description="Base daily trading volume in tokens")
    volume_multiplier: float = Field(1.0, ge=0.1, le=100.0, description="Volume adjustment multiplier")


class MonteCarloConfig(BaseModel):
    """Monte Carlo simulation configuration."""
    enabled: bool = False
    num_trials: int = Field(100, ge=10, le=1000)
    variance_level: Literal["low", "medium", "high"] = "medium"
    seed: Optional[int] = Field(None, ge=0)
    confidence_levels: List[int] = Field(default_factory=lambda: [10, 50, 90], description="Percentiles for confidence bands")


class ABMSimulationRequest(BaseModel):
    """
    Complete ABM simulation request.

    Reuses token and buckets from existing SimulationConfig,
    adds ABM-specific parameters.
    """
    # Token and bucket configuration with validation
    token: TokenConfig
    buckets: List[BucketConfig]

    # ABM-specific
    abm: ABMConfig = Field(default_factory=ABMConfig)

    # Optional cohort profile overrides
    cohort_profiles: Optional[Dict[str, CohortProfileOverride]] = None

    # Monte Carlo (Phase 6)
    monte_carlo: Optional[MonteCarloConfig] = None

    @field_validator('buckets')
    @classmethod
    def validate_buckets_not_empty(cls, v: List[BucketConfig]) -> List[BucketConfig]:
        """Ensure at least one bucket is provided."""
        if not v or len(v) == 0:
            raise ValueError('At least one bucket must be provided')
        return v

    @field_validator('buckets')
    @classmethod
    def validate_allocation_total(cls, v: List[BucketConfig]) -> List[BucketConfig]:
        """Validate that total allocation doesn't exceed 100%."""
        total_allocation = sum(bucket.allocation for bucket in v)
        if total_allocation > 100.01:  # Allow small floating point error
            raise ValueError(f'Total allocation ({total_allocation}%) exceeds 100%')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "token": {
                    "name": "MyToken",
                    "total_supply": 1000000000,
                    "start_date": "2025-01-01",
                    "horizon_months": 36
                },
                "buckets": [
                    {
                        "bucket": "Team",
                        "allocation": 20,
                        "tge_unlock_pct": 0,
                        "cliff_months": 12,
                        "vesting_months": 24
                    },
                    {
                        "bucket": "VC",
                        "allocation": 15,
                        "tge_unlock_pct": 10,
                        "cliff_months": 6,
                        "vesting_months": 18
                    },
                    {
                        "bucket": "Community",
                        "allocation": 40,
                        "tge_unlock_pct": 20,
                        "cliff_months": 0,
                        "vesting_months": 12
                    }
                ],
                "abm": {
                    "pricing_model": "eoe",
                    "agents_per_cohort": 50,
                    "store_cohort_details": True
                }
            }
        }


class LenientABMConfig(BaseModel):
    """Lenient ABM config for validation endpoint - accepts partial configs."""
    token: Dict[str, Any]
    buckets: List[Dict[str, Any]]
    abm: ABMConfig = Field(default_factory=ABMConfig)
    cohort_profiles: Optional[Dict[str, CohortProfileOverride]] = None
    monte_carlo: Optional[MonteCarloConfig] = None


class ABMValidateRequest(BaseModel):
    """Request for ABM config validation."""
    config: LenientABMConfig
