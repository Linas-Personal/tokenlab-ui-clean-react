"""Token holder agent with vesting and behavioral decision-making."""
from dataclasses import dataclass
from collections import deque
from typing import Dict, Any, Deque, Optional
import logging

from app.abm.core.controller import ABMController
from app.abm.vesting.vesting_schedule import VestingSchedule
from app.abm.dynamics.token_economy import TokenEconomy

logger = logging.getLogger(__name__)


@dataclass
class TokenHolderAttributes:
    agent_id: str
    cohort: str
    risk_tolerance: float
    hold_time_preference: float
    price_sensitivity: float
    staking_propensity: float
    allocation_tokens: float
    sell_pressure_base: float
    cliff_shock_multiplier: float
    take_profit_threshold: float
    stop_loss_threshold: float
    scaling_weight: float = 1.0


@dataclass
class AgentAction:
    agent_id: str
    sell_tokens: float
    stake_tokens: float
    hold_tokens: float
    scaling_weight: float = 1.0


class TokenHolderAgent(ABMController):
    """Token holder with vesting schedule and behavioral decision-making."""

    def __init__(self, attributes: TokenHolderAttributes, vesting_schedule: VestingSchedule):
        super().__init__()
        self.attrs = attributes
        self.vesting = vesting_schedule
        self.locked_balance = attributes.allocation_tokens
        self.unlocked_balance = 0.0
        self.staked_balance = 0.0
        self.sold_cumulative = 0.0
        self.price_history: Deque[float] = deque(maxlen=12)
        self.initial_price: Optional[float] = None

        logger.debug(
            f"Agent {attributes.agent_id} created: cohort={attributes.cohort}, "
            f"allocation={attributes.allocation_tokens:,.0f}, "
            f"risk_tolerance={attributes.risk_tolerance:.2f}"
        )

    async def execute(self) -> AgentAction:
        """
        Execute one time step of agent behavior.

        Returns:
            AgentAction with sell/stake/hold decisions
        """
        # 1. Process vesting unlock
        newly_unlocked = self.vesting.advance_month()
        self.unlocked_balance += newly_unlocked
        self.locked_balance = self.vesting.get_remaining_locked()

        # 2. Get current market state (from linked TokenEconomy)
        token_economy = self.get_dependency(TokenEconomy)
        current_price = token_economy.price

        # Track price history
        self.price_history.append(current_price)
        if self.initial_price is None:
            self.initial_price = current_price

        # 3. Decide sell amount
        sell_amount = self._decide_sell_amount(current_price, newly_unlocked)

        # 4. Decide stake amount (from remaining unlocked balance)
        stake_amount = self._decide_stake_amount(self.unlocked_balance - sell_amount)

        # 5. Update balances
        self.unlocked_balance -= (sell_amount + stake_amount)
        self.staked_balance += stake_amount
        self.sold_cumulative += sell_amount

        # 6. Increment iteration counter
        self.iteration += 1

        return AgentAction(
            agent_id=self.attrs.agent_id,
            sell_tokens=sell_amount,
            stake_tokens=stake_amount,
            hold_tokens=self.unlocked_balance,
            scaling_weight=self.attrs.scaling_weight
        )

    def _decide_sell_amount(self, current_price: float, newly_unlocked: float) -> float:
        base_sell = newly_unlocked * self.attrs.sell_pressure_base
        price_factor = self._calculate_price_trigger_factor(current_price)
        cliff_factor = self._calculate_cliff_factor()
        risk_mod = max(0.5, min(1.5, 1.0 + (self.attrs.risk_tolerance - 0.5) * 0.5))
        sell_amount = base_sell * price_factor * cliff_factor * risk_mod
        return max(0.0, min(sell_amount, self.unlocked_balance))

    def _calculate_price_trigger_factor(self, current_price: float) -> float:
        if not self.initial_price:
            return 1.0

        price_change_pct = (current_price - self.initial_price) / self.initial_price

        if price_change_pct > self.attrs.take_profit_threshold:
            return 1.0 + (0.2 * self.attrs.price_sensitivity)

        if price_change_pct < self.attrs.stop_loss_threshold:
            return 1.0 + (0.3 * self.attrs.price_sensitivity)

        return 1.0

    def _calculate_cliff_factor(self) -> float:
        return self.attrs.cliff_shock_multiplier if self.vesting.is_cliff_month() else 1.0

    def _decide_stake_amount(self, available_balance: float) -> float:
        return max(0.0, available_balance * self.attrs.staking_propensity)

    def snapshot_state(self) -> Dict[str, Any]:
        state = super().snapshot_state()
        state.update({
            "locked_balance": self.locked_balance,
            "unlocked_balance": self.unlocked_balance,
            "staked_balance": self.staked_balance,
            "sold_cumulative": self.sold_cumulative,
            "price_history": list(self.price_history),
            "initial_price": self.initial_price,
            "vesting_state": self.vesting.snapshot_state()
        })
        return state

    def restore_state(self, state: Dict[str, Any]) -> None:
        super().restore_state(state)
        self.locked_balance = state["locked_balance"]
        self.unlocked_balance = state["unlocked_balance"]
        self.staked_balance = state["staked_balance"]
        self.sold_cumulative = state["sold_cumulative"]
        self.price_history = deque(state["price_history"], maxlen=12)
        self.initial_price = state["initial_price"]
        self.vesting.restore_state(state["vesting_state"])

    def __repr__(self) -> str:
        return (
            f"TokenHolderAgent({self.attrs.agent_id}, cohort={self.attrs.cohort}, "
            f"locked={self.locked_balance:,.0f}, unlocked={self.unlocked_balance:,.0f}, "
            f"sold={self.sold_cumulative:,.0f})"
        )
