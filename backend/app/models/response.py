"""
Pydantic response models for API responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any


class BucketResult(BaseModel):
    """Single row of bucket-level results."""
    month_index: int
    date: str
    bucket: str
    allocation_tokens: float
    unlocked_this_month: float
    unlocked_cumulative: float
    locked_remaining: float
    sell_pressure_effective: float
    expected_sell_this_month: float
    expected_circulating_cumulative: float


class GlobalMetric(BaseModel):
    """Single row of global metrics."""
    month_index: int
    date: str
    total_unlocked: float
    total_expected_sell: float
    expected_circulating_total: float
    expected_circulating_pct: float
    sell_volume_ratio: Optional[float] = None
    current_price: Optional[float] = None
    staked_amount: Optional[float] = None
    liquidity_deployed: Optional[float] = None
    treasury_balance: Optional[float] = None


class SummaryCards(BaseModel):
    """Summary statistics for dashboard cards."""
    max_unlock_tokens: float
    max_unlock_month: int
    max_sell_tokens: float
    max_sell_month: int
    circ_12_pct: Optional[float] = None  # None if horizon < 12
    circ_24_pct: Optional[float] = None  # None if horizon < 24
    circ_end_pct: Optional[float] = None  # None if simulation fails


class SimulationData(BaseModel):
    """Simulation results data."""
    bucket_results: List[BucketResult]
    global_metrics: List[GlobalMetric]
    summary_cards: SummaryCards


class SimulateResponse(BaseModel):
    """Response model for simulation endpoint."""
    status: str = "success"
    execution_time_ms: float
    warnings: List[str]
    data: SimulationData


class ValidationResponse(BaseModel):
    """Response model for config validation endpoint."""
    valid: bool
    warnings: List[str]
    errors: List[str]


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    version: str


class ErrorResponse(BaseModel):
    """Response model for errors."""
    status: str = "error"
    error_type: str
    message: str
    details: Optional[Any] = None
