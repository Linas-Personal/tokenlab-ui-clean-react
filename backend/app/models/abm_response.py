"""
Pydantic response models for ABM API.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class ABMGlobalMetric(BaseModel):
    """Global metrics for one time step."""
    month_index: int
    date: str
    price: float
    circulating_supply: float
    total_unlocked: float
    total_sold: float
    total_staked: float
    total_held: float


class ABMCohortMetric(BaseModel):
    """Cohort-level metrics for one time step."""
    month_index: int
    cohort_name: str
    total_sold: float
    total_staked: float
    total_held: float
    num_agents: int


class ABMAgentSnapshot(BaseModel):
    """Individual agent state snapshot (optional, large)."""
    agent_id: str
    cohort: str
    month_index: int
    locked_balance: float
    unlocked_balance: float
    staked_balance: float
    sold_cumulative: float


class ABMSummaryCards(BaseModel):
    """Summary statistics for the simulation."""
    max_sell_month: int
    max_sell_tokens: float
    final_price: float
    final_circulating_supply: float
    total_tokens_sold: float
    average_price: float


class ABMSimulationResults(BaseModel):
    """
    Complete ABM simulation results.

    Includes:
    - Global metrics (time series)
    - Cohort-level breakdown (optional)
    - Agent-level details (optional, large)
    - Summary statistics
    """
    # Global time series
    global_metrics: List[ABMGlobalMetric]

    # Cohort-level breakdown (optional)
    cohort_metrics: Optional[List[ABMCohortMetric]] = None

    # Agent-level details (optional, very large)
    agent_snapshots: Optional[List[ABMAgentSnapshot]] = None

    # Summary statistics
    summary: ABMSummaryCards

    # Metadata
    execution_time_seconds: float
    num_agents: int
    num_cohorts: int
    warnings: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "global_metrics": [
                    {
                        "month_index": 0,
                        "date": "2025-01-01",
                        "price": 1.0,
                        "circulating_supply": 200000000,
                        "total_unlocked": 200000000,
                        "total_sold": 50000000,
                        "total_staked": 30000000,
                        "total_held": 120000000
                    }
                ],
                "summary": {
                    "max_sell_month": 12,
                    "max_sell_tokens": 80000000,
                    "final_price": 0.85,
                    "final_circulating_supply": 750000000,
                    "total_tokens_sold": 400000000,
                    "average_price": 0.92
                },
                "execution_time_seconds": 5.2,
                "num_agents": 150,
                "num_cohorts": 3,
                "warnings": []
            }
        }


class JobStatus(str, Enum):
    """Job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    status: JobStatus
    progress_pct: Optional[float] = None
    current_month: Optional[int] = None
    total_months: Optional[int] = None
    error: Optional[str] = None


class JobSubmissionResponse(BaseModel):
    """Response when submitting a job."""
    job_id: str
    status: JobStatus
    status_url: str
    stream_url: Optional[str] = None
    cached: bool = False


from enum import Enum
