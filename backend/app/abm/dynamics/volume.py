"""
Dynamic Volume Controller.

Calculates transaction volume based on market conditions.
Supports two models:
1. Proportional: Volume scales with circulating supply
2. Constant: Fixed daily volume

Used by EOEPricingController to determine market demand.
"""
from dataclasses import dataclass
from typing import Literal
import logging

from app.abm.core.controller import ABMController
from app.abm.dynamics.token_economy import TokenEconomy

logger = logging.getLogger(__name__)


@dataclass
class VolumeConfigData:
    """Volume calculation configuration."""
    volume_model: Literal["proportional", "constant"] = "proportional"
    base_daily_volume: float = 10_000_000.0
    volume_multiplier: float = 1.0


class VolumeController(ABMController):
    """
    Calculates daily transaction volume.

    Two models:
    1. Proportional: Volume scales with circulating supply ratio
       - volume = base_daily_volume * (circulating / total_supply) * multiplier
       - More realistic: as more tokens circulate, trading volume increases

    2. Constant: Fixed daily volume
       - volume = base_daily_volume * multiplier
       - Simpler model: assumes constant market activity

    The calculated volume represents the fiat value of daily transactions,
    used in EOE pricing model (P = Volume / (Supply * Velocity))
    """

    def __init__(self, config: VolumeConfigData):
        super().__init__()
        self.config = config
        logger.info(
            f"VolumeController initialized: model={config.volume_model}, "
            f"base={config.base_daily_volume:,.0f}, multiplier={config.volume_multiplier}"
        )

    async def execute(self) -> float:
        """
        Calculate current transaction volume in tokens.

        Returns:
            Transaction volume (float): Daily trading volume in tokens
        """
        token_economy = self.get_dependency(TokenEconomy)

        if self.config.volume_model == "proportional":
            # Volume proportional to circulating supply
            # Normalize to total supply to get ratio
            supply_ratio = token_economy.circulating_supply / token_economy.total_supply
            volume = self.config.base_daily_volume * supply_ratio * self.config.volume_multiplier

            logger.debug(
                f"Proportional volume: supply_ratio={supply_ratio:.4f}, "
                f"volume={volume:,.0f}"
            )
        else:
            # Constant volume
            volume = self.config.base_daily_volume * self.config.volume_multiplier

            logger.debug(f"Constant volume: {volume:,.0f}")

        return max(0.0, volume)

    def reset(self):
        """Reset volume controller state (none needed)."""
        pass

    def snapshot_state(self) -> dict:
        """Capture current state for persistence."""
        return {
            "volume_model": self.config.volume_model,
            "base_daily_volume": self.config.base_daily_volume,
            "volume_multiplier": self.config.volume_multiplier
        }

    def restore_state(self, state: dict):
        """Restore state from snapshot."""
        self.config.volume_model = state["volume_model"]
        self.config.base_daily_volume = state["base_daily_volume"]
        self.config.volume_multiplier = state["volume_multiplier"]
