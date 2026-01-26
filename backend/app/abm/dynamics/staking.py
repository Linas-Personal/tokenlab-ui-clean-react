"""
Staking Pool Controller - Dynamic staking with variable APY.

Adapted from TokenLab's SupplyStaker concept with enhancements:
- Dynamic APY based on pool utilization
- Capacity limits
- Lockup periods
- Reward distribution
"""
from dataclasses import dataclass
from typing import Dict, Any, List
import logging

from app.abm.core.controller import ABMController
from app.abm.dynamics.token_economy import TokenEconomy

logger = logging.getLogger(__name__)


@dataclass
class StakeLock:
    """Individual stake lock entry."""
    amount: float
    locked_until_month: int
    apy: float  # APY at time of locking


@dataclass
class StakingConfig:
    """Staking pool configuration."""
    base_apy: float = 0.12  # 12% base APY
    max_capacity_pct: float = 0.5  # 50% of total supply
    lockup_months: int = 6  # 6 month lockup
    reward_source: str = "emission"  # "emission" or "treasury"

    # Dynamic APY parameters
    apy_multiplier_at_empty: float = 1.5  # 150% of base when empty
    apy_multiplier_at_full: float = 0.5  # 50% of base when full


class StakingPool(ABMController):
    """
    Dynamic staking pool with capacity management and variable APY.

    Features:
    - Variable APY based on utilization (incentivize early stakers)
    - Capacity limits (prevent over-staking)
    - Lockup periods (tokens locked for N months)
    - Reward distribution (from emissions or treasury)
    - Reduces circulating supply (staked tokens removed)
    """

    def __init__(self, config: StakingConfig, total_supply: float):
        """
        Initialize staking pool.

        Args:
            config: Staking configuration
            total_supply: Total token supply (for capacity calculation)
        """
        super().__init__(config)
        self.config = config

        # Capacity
        self.max_capacity = total_supply * config.max_capacity_pct
        self.total_staked = 0.0

        # Stake locks (will unlock after lockup period)
        self.locked_stakes: List[StakeLock] = []

        # Cumulative rewards distributed
        self.total_rewards_distributed = 0.0

        logger.info(
            f"StakingPool initialized: "
            f"base_apy={config.base_apy:.1%}, "
            f"max_capacity={self.max_capacity:,.0f}, "
            f"lockup={config.lockup_months}m"
        )

    @property
    def remaining_capacity(self) -> float:
        """Get remaining staking capacity."""
        return max(0.0, self.max_capacity - self.total_staked)

    @property
    def utilization_pct(self) -> float:
        """Get pool utilization percentage (0-100)."""
        if self.max_capacity == 0:
            return 0.0
        return (self.total_staked / self.max_capacity) * 100.0

    @property
    def current_apy(self) -> float:
        """
        Calculate current APY based on utilization.

        APY decreases as pool fills (incentivize early staking).
        Empty pool: 150% of base APY
        Full pool: 50% of base APY
        """
        utilization = self.total_staked / self.max_capacity if self.max_capacity > 0 else 0

        # Linear interpolation between empty and full multipliers
        multiplier = (
            self.config.apy_multiplier_at_empty * (1 - utilization) +
            self.config.apy_multiplier_at_full * utilization
        )

        return self.config.base_apy * multiplier

    async def execute(self, new_stake_amount: float = 0.0) -> Dict[str, float]:
        """
        Execute one staking pool iteration.

        1. Process new stakes (up to capacity)
        2. Process unlock (lockup expired)
        3. Distribute rewards
        4. Update token economy

        Args:
            new_stake_amount: Tokens to stake this month

        Returns:
            Dictionary with staking metrics
        """
        token_economy = self.get_dependency(TokenEconomy)

        # 1. Process new stakes (up to remaining capacity)
        actual_staked = min(new_stake_amount, self.remaining_capacity)

        if actual_staked > 0:
            # Lock stake for N months at current APY
            lock = StakeLock(
                amount=actual_staked,
                locked_until_month=self.iteration + self.config.lockup_months,
                apy=self.current_apy
            )
            self.locked_stakes.append(lock)
            self.total_staked += actual_staked

            logger.debug(
                f"New stake: {actual_staked:,.0f} tokens locked until month "
                f"{lock.locked_until_month} at {lock.apy:.1%} APY"
            )

        rejected_stake = new_stake_amount - actual_staked
        if rejected_stake > 0:
            logger.debug(
                f"Rejected stake: {rejected_stake:,.0f} tokens (capacity full)"
            )

        # 2. Process unlocks (lockup period expired)
        unlocked_stakes = [
            stake for stake in self.locked_stakes
            if stake.locked_until_month <= self.iteration
        ]

        total_unlocked_principal = 0.0
        total_rewards = 0.0

        for stake in unlocked_stakes:
            # Calculate rewards
            # APY is annualized, so monthly rate = APY / 12
            # Rewards = principal * (apy / 12) * lockup_months
            monthly_rate = stake.apy / 12.0
            rewards = stake.amount * monthly_rate * self.config.lockup_months

            total_unlocked_principal += stake.amount
            total_rewards += rewards

            logger.debug(
                f"Unlock: {stake.amount:,.0f} principal + {rewards:,.0f} rewards "
                f"(APY={stake.apy:.1%})"
            )

            # Remove from pool
            self.total_staked -= stake.amount
            self.locked_stakes.remove(stake)

        # 3. Return to circulation (principal + rewards)
        if total_unlocked_principal > 0 or total_rewards > 0:
            return_to_circulation = total_unlocked_principal + total_rewards
            token_economy.update_circulating_supply(return_to_circulation)

            self.total_rewards_distributed += total_rewards

            logger.debug(
                f"Returned to circulation: {return_to_circulation:,.0f} "
                f"(principal={total_unlocked_principal:,.0f}, "
                f"rewards={total_rewards:,.0f})"
            )

        # 4. Increment iteration
        self.iteration += 1

        return {
            "new_staked": actual_staked,
            "rejected_stake": rejected_stake,
            "unlocked_principal": total_unlocked_principal,
            "rewards_paid": total_rewards,
            "total_staked": self.total_staked,
            "current_apy": self.current_apy,
            "utilization_pct": self.utilization_pct
        }

    def snapshot_state(self) -> Dict[str, Any]:
        """Snapshot staking pool state."""
        state = super().snapshot_state()
        state.update({
            "total_staked": self.total_staked,
            "total_rewards_distributed": self.total_rewards_distributed,
            "locked_stakes": [
                {"amount": s.amount, "locked_until": s.locked_until_month, "apy": s.apy}
                for s in self.locked_stakes
            ]
        })
        return state

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore staking pool state."""
        super().restore_state(state)
        self.total_staked = state["total_staked"]
        self.total_rewards_distributed = state["total_rewards_distributed"]
        self.locked_stakes = [
            StakeLock(
                amount=s["amount"],
                locked_until_month=s["locked_until"],
                apy=s["apy"]
            )
            for s in state["locked_stakes"]
        ]

    def __repr__(self) -> str:
        return (
            f"StakingPool(staked={self.total_staked:,.0f}, "
            f"utilization={self.utilization_pct:.1f}%, "
            f"apy={self.current_apy:.1%}, "
            f"locks={len(self.locked_stakes)})"
        )
