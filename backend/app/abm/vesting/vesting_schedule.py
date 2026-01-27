"""
Vesting Schedule Logic for Individual Agents.

Handles token unlock timing for individual agent allocations.
"""
from dataclasses import dataclass
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class VestingConfig:
    """Configuration for a vesting schedule."""
    total_allocation: float
    tge_unlock_pct: float  # 0-100
    cliff_months: int
    vesting_months: int
    unlock_type: str = "linear"  # Currently only linear supported


class VestingSchedule:
    """
    Manages vesting schedule for an individual agent's token allocation.

    Tracks:
    - What has already unlocked
    - What unlocks this month
    - What remains locked
    """

    def __init__(self, config: VestingConfig):
        """
        Initialize vesting schedule.

        Args:
            config: Vesting configuration
        """
        self.config = config

        # Calculate TGE unlock amount
        self.tge_amount = config.total_allocation * (config.tge_unlock_pct / 100.0)

        # Calculate remaining to vest after TGE
        self.post_tge_amount = config.total_allocation - self.tge_amount

        # Calculate monthly unlock rate (linear)
        if config.vesting_months > 0:
            self.monthly_unlock_rate = self.post_tge_amount / config.vesting_months
        else:
            self.monthly_unlock_rate = 0.0

        # State
        self.current_month = 0
        self.cumulative_unlocked = 0.0

        logger.debug(
            f"Vesting schedule: total={config.total_allocation:,.0f}, "
            f"TGE={self.tge_amount:,.0f} ({config.tge_unlock_pct}%), "
            f"cliff={config.cliff_months}m, vesting={config.vesting_months}m, "
            f"monthly_rate={self.monthly_unlock_rate:,.0f}"
        )

    def get_unlock_for_month(self, month_index: int) -> float:
        """
        Calculate token unlock amount for a specific month.

        Args:
            month_index: Month number (0-indexed, 0 = TGE)

        Returns:
            Number of tokens that unlock this month
        """
        unlock_amount = 0.0

        # TGE unlock at month 0
        if month_index == 0:
            unlock_amount += self.tge_amount

            # If cliff is 0, first vesting also happens at month 0
            if self.config.cliff_months == 0 and self.config.vesting_months > 0:
                unlock_amount += self.monthly_unlock_rate

            return unlock_amount

        # During cliff period (after TGE), no unlock
        if month_index < self.config.cliff_months:
            return 0.0

        # After cliff period, calculate vesting unlocks
        # For cliff=0: months 1, 2, 3... unlock vesting months 2, 3, 4...
        # For cliff>0: month==cliff unlocks vesting month 1, then continue
        if self.config.cliff_months == 0:
            # Already unlocked month 1 at month 0, so month_index corresponds to vesting month (month_index + 1)
            vesting_month_index = month_index  # month 1 -> vesting month 2 (0-indexed: month 1)
        else:
            # First unlock happens at cliff month (vesting month 1), then continue
            vesting_month_index = month_index - self.config.cliff_months

        if vesting_month_index < self.config.vesting_months:
            return self.monthly_unlock_rate
        else:
            # Vesting complete
            return 0.0

    def advance_month(self) -> float:
        """
        Advance to next month and return unlock amount.

        Returns:
            Tokens unlocked this month
        """
        unlock_amount = self.get_unlock_for_month(self.current_month)
        self.cumulative_unlocked += unlock_amount
        self.current_month += 1
        return unlock_amount

    def is_cliff_month(self) -> bool:
        """
        Check if current month is the cliff month (first unlock after cliff).

        Returns:
            True if this is the cliff unlock month
        """
        return self.current_month == self.config.cliff_months and self.config.cliff_months > 0

    def get_remaining_locked(self) -> float:
        """
        Get amount still locked.

        Returns:
            Tokens remaining locked
        """
        return self.config.total_allocation - self.cumulative_unlocked

    def snapshot_state(self) -> Dict[str, Any]:
        """
        Snapshot current vesting state.

        Returns:
            State dictionary
        """
        return {
            "current_month": self.current_month,
            "cumulative_unlocked": self.cumulative_unlocked
        }

    def restore_state(self, state: Dict[str, Any]) -> None:
        """
        Restore vesting state.

        Args:
            state: State from snapshot_state()
        """
        self.current_month = state["current_month"]
        self.cumulative_unlocked = state["cumulative_unlocked"]

    @classmethod
    def from_bucket_config(cls, bucket_config: Dict[str, Any], allocation_tokens: float) -> "VestingSchedule":
        """
        Create VestingSchedule from bucket configuration.

        Args:
            bucket_config: Bucket config dict (from API request)
            allocation_tokens: Number of tokens allocated to this agent

        Returns:
            VestingSchedule instance
        """
        config = VestingConfig(
            total_allocation=allocation_tokens,
            tge_unlock_pct=bucket_config["tge_unlock_pct"],
            cliff_months=bucket_config["cliff_months"],
            vesting_months=bucket_config["vesting_months"],
            unlock_type=bucket_config.get("unlock_type", "linear")
        )
        return cls(config)

    def __repr__(self) -> str:
        return (
            f"VestingSchedule(month={self.current_month}, "
            f"unlocked={self.cumulative_unlocked:,.0f}, "
            f"locked={self.get_remaining_locked():,.0f})"
        )
