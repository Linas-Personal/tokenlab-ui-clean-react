"""
Token Holder Agent - Individual token holder with heterogeneous behaviors.

Each agent has unique attributes (risk tolerance, hold time, price sensitivity, etc.)
and makes decisions about selling and staking based on:
- Vesting schedule unlocks
- Current price vs historical
- Individual behavioral parameters
- Cohort characteristics
"""
from dataclasses import dataclass, field
from collections import deque
from typing import Dict, Any, Deque, Optional
import logging

from app.abm.core.controller import ABMController
from app.abm.vesting.vesting_schedule import VestingSchedule
from app.abm.dynamics.token_economy import TokenEconomy

logger = logging.getLogger(__name__)


@dataclass
class TokenHolderAttributes:
    """
    Attributes defining an individual token holder's characteristics.

    These are sampled from cohort distributions to create heterogeneity.
    """
    agent_id: str
    cohort: str  # "Team", "VC", "Community", etc.

    # Behavioral parameters (0-1)
    risk_tolerance: float  # Higher = more likely to hold through volatility
    hold_time_preference: float  # Preferred holding time in months
    price_sensitivity: float  # How strongly they react to price changes
    staking_propensity: float  # Likelihood to stake vs sell/hold

    # Token allocation
    allocation_tokens: float

    # Sell behavior parameters
    sell_pressure_base: float  # Base % of unlock to sell (0-1)
    cliff_shock_multiplier: float  # Multiplier on cliff month
    take_profit_threshold: float  # % gain to trigger extra selling
    stop_loss_threshold: float  # % loss to trigger extra selling

    # Scaling weight (for meta-agents representing multiple holders)
    scaling_weight: float = 1.0


@dataclass
class AgentAction:
    """Result of agent execution for one time step."""
    agent_id: str
    sell_tokens: float
    stake_tokens: float
    hold_tokens: float
    scaling_weight: float = 1.0


class TokenHolderAgent(ABMController):
    """
    Individual token holder agent with vesting schedule and decision-making.

    The agent:
    1. Receives token unlocks according to vesting schedule
    2. Decides how much to sell based on behavioral parameters and market conditions
    3. Decides how much to stake
    4. Tracks memory of price history for adaptive behavior
    """

    def __init__(self, attributes: TokenHolderAttributes, vesting_schedule: VestingSchedule):
        """
        Initialize token holder agent.

        Args:
            attributes: Agent attributes
            vesting_schedule: Vesting schedule for this agent
        """
        super().__init__()
        self.attrs = attributes
        self.vesting = vesting_schedule

        # Balance tracking
        self.locked_balance = attributes.allocation_tokens
        self.unlocked_balance = 0.0
        self.staked_balance = 0.0
        self.sold_cumulative = 0.0

        # Memory for adaptive behavior (last 12 months)
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
        sell_amount = await self._decide_sell_amount(current_price, newly_unlocked)

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

    async def _decide_sell_amount(self, current_price: float, newly_unlocked: float) -> float:
        """
        Decide how much to sell this month.

        Selling logic:
        - Base sell = newly_unlocked * sell_pressure_base
        - Adjusted by price triggers (take profit / stop loss)
        - Adjusted by cliff shock (if cliff month)
        - Modulated by risk tolerance

        Args:
            current_price: Current token price
            newly_unlocked: Tokens newly unlocked this month

        Returns:
            Tokens to sell (capped at unlocked_balance)
        """
        # Base sell pressure
        base_sell = newly_unlocked * self.attrs.sell_pressure_base

        # Price trigger factor
        price_factor = self._calculate_price_trigger_factor(current_price)

        # Cliff shock factor
        cliff_factor = self._calculate_cliff_factor()

        # Risk tolerance modulation
        # High risk tolerance = less selling (hold more)
        # Low risk tolerance = more selling (risk-averse)
        risk_mod = 1.0 + (self.attrs.risk_tolerance - 0.5) * 0.5
        risk_mod = max(0.5, min(1.5, risk_mod))  # Clamp to [0.5, 1.5]

        # Final sell amount
        sell_amount = base_sell * price_factor * cliff_factor * risk_mod

        # Cap at available unlocked balance
        sell_amount = min(sell_amount, self.unlocked_balance)

        return max(0.0, sell_amount)

    def _calculate_price_trigger_factor(self, current_price: float) -> float:
        """
        Calculate price trigger factor for selling.

        - If price up > take_profit_threshold: increase selling (take profits)
        - If price down > stop_loss_threshold: increase selling (cut losses)
        - Otherwise: neutral (factor = 1.0)

        Returns:
            Multiplier for sell amount (>= 1.0)
        """
        if self.initial_price is None or self.initial_price == 0:
            return 1.0

        price_change_pct = (current_price - self.initial_price) / self.initial_price

        # Take profit trigger
        if price_change_pct > self.attrs.take_profit_threshold:
            # Price is up significantly, take profits
            # Higher price sensitivity = stronger reaction
            extra_sell = 0.2 * self.attrs.price_sensitivity
            return 1.0 + extra_sell

        # Stop loss trigger
        elif price_change_pct < self.attrs.stop_loss_threshold:
            # Price is down significantly, cut losses
            extra_sell = 0.3 * self.attrs.price_sensitivity
            return 1.0 + extra_sell

        return 1.0

    def _calculate_cliff_factor(self) -> float:
        """
        Calculate cliff shock factor.

        On the first unlock after cliff, agents often sell more aggressively.

        Returns:
            Multiplier for sell amount (>= 1.0)
        """
        if self.vesting.is_cliff_month():
            return self.attrs.cliff_shock_multiplier
        return 1.0

    def _decide_stake_amount(self, available_balance: float) -> float:
        """
        Decide how much to stake.

        Staking decision based on staking_propensity (random component
        would be added in Monte Carlo mode).

        Args:
            available_balance: Tokens available to stake (after selling)

        Returns:
            Tokens to stake
        """
        # Simple proportional staking based on propensity
        stake_amount = available_balance * self.attrs.staking_propensity

        return max(0.0, stake_amount)

    def snapshot_state(self) -> Dict[str, Any]:
        """
        Snapshot agent state for persistence.

        Returns:
            State dictionary
        """
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
        """
        Restore agent state from snapshot.

        Args:
            state: State from snapshot_state()
        """
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
