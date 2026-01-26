"""
Token Economy State Management.

Central state object that all ABM components interact with.
Adapted from TokenLab's TokenEconomy class.
"""
from dataclasses import dataclass, field
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class TokenEconomyConfig:
    """Configuration for token economy."""
    total_supply: float
    initial_price: float = 1.0
    initial_circulating_supply: float = 0.0


class TokenEconomy:
    """
    Central state manager for the token economy.

    This is the shared state that agents and controllers read from and write to.
    It represents the global token market state at any point in time.

    Key properties:
    - circulating_supply: Tokens available in the market
    - price: Current token price (dynamically updated)
    - total_sell_pressure: Aggregate selling from all agents this month
    - iteration: Current simulation month
    """

    def __init__(self, config: TokenEconomyConfig):
        """
        Initialize token economy.

        Args:
            config: Token economy configuration
        """
        self.config = config

        # Core state
        self.iteration = 0
        self.total_supply = config.total_supply
        self.circulating_supply = config.initial_circulating_supply
        self.price = config.initial_price

        # Market dynamics (updated each iteration by agents)
        self.total_sell_pressure = 0.0  # Tokens sold this month
        self.total_stake_pressure = 0.0  # Tokens staked this month
        self.total_unlock_this_month = 0.0  # Tokens unlocked this month

        # Transaction tracking (for EOE pricing)
        self.transactions_value_in_fiat = 0.0  # Total fiat volume traded

        # Historical data (for agent adaptive behavior)
        self.price_history = [config.initial_price]
        self.supply_history = [config.initial_circulating_supply]

        logger.info(
            f"TokenEconomy initialized: "
            f"supply={config.total_supply:,.0f}, "
            f"price=${config.initial_price:.4f}, "
            f"circulating={config.initial_circulating_supply:,.0f}"
        )

    def reset_monthly_pressures(self) -> None:
        """
        Reset monthly aggregates at start of each iteration.

        Called by ABMSimulationLoop before agents execute.
        """
        self.total_sell_pressure = 0.0
        self.total_stake_pressure = 0.0
        self.total_unlock_this_month = 0.0
        self.transactions_value_in_fiat = 0.0

    def update_price(self, new_price: float) -> None:
        """
        Update current price and record in history.

        Args:
            new_price: New price value
        """
        self.price = max(0.01, new_price)  # Floor at 1 cent
        self.price_history.append(self.price)

    def update_circulating_supply(self, amount: float) -> None:
        """
        Update circulating supply and record in history.

        Args:
            amount: Change in circulating supply (can be negative for burns)
        """
        self.circulating_supply = max(0.0, self.circulating_supply + amount)
        self.supply_history.append(self.circulating_supply)

    def get_price_change_pct(self, lookback_months: int = 1) -> float:
        """
        Calculate price change percentage over lookback period.

        Args:
            lookback_months: Number of months to look back

        Returns:
            Price change as percentage (-1.0 to +infinity)
        """
        if len(self.price_history) < lookback_months + 1:
            return 0.0

        old_price = self.price_history[-(lookback_months + 1)]
        if old_price == 0:
            return 0.0

        return (self.price - old_price) / old_price

    def get_current_market_cap(self) -> float:
        """
        Calculate current market capitalization.

        Returns:
            Market cap in fiat
        """
        return self.circulating_supply * self.price

    def snapshot_state(self) -> Dict[str, Any]:
        """
        Snapshot current state for persistence.

        Returns:
            State dictionary
        """
        return {
            "iteration": self.iteration,
            "total_supply": self.total_supply,
            "circulating_supply": self.circulating_supply,
            "price": self.price,
            "total_sell_pressure": self.total_sell_pressure,
            "total_stake_pressure": self.total_stake_pressure,
            "total_unlock_this_month": self.total_unlock_this_month,
            "transactions_value_in_fiat": self.transactions_value_in_fiat,
            "price_history": self.price_history.copy(),
            "supply_history": self.supply_history.copy()
        }

    def restore_state(self, state: Dict[str, Any]) -> None:
        """
        Restore state from snapshot.

        Args:
            state: State from snapshot_state()
        """
        self.iteration = state["iteration"]
        self.total_supply = state["total_supply"]
        self.circulating_supply = state["circulating_supply"]
        self.price = state["price"]
        self.total_sell_pressure = state["total_sell_pressure"]
        self.total_stake_pressure = state["total_stake_pressure"]
        self.total_unlock_this_month = state["total_unlock_this_month"]
        self.transactions_value_in_fiat = state["transactions_value_in_fiat"]
        self.price_history = state["price_history"]
        self.supply_history = state["supply_history"]

    def __repr__(self) -> str:
        return (
            f"TokenEconomy(month={self.iteration}, "
            f"price=${self.price:.4f}, "
            f"circ_supply={self.circulating_supply:,.0f}, "
            f"sell_pressure={self.total_sell_pressure:,.0f})"
        )
