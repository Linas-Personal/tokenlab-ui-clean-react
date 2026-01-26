"""
Dynamic Pricing Models for ABM Simulations.

Adapted from TokenLab's PriceFunction classes.
"""
from enum import Enum
from typing import Dict, Any
import logging

from app.abm.core.controller import ABMController
from app.abm.dynamics.token_economy import TokenEconomy

logger = logging.getLogger(__name__)


class PricingModel(str, Enum):
    """Available pricing models."""
    EOE = "eoe"  # Equation of Exchange (MV=PQ)
    BONDING_CURVE = "bonding_curve"  # P = k * S^n
    ISSUANCE_CURVE = "issuance_curve"  # P = P0 * (1 + S/S_max)^alpha
    CONSTANT = "constant"  # Fixed price


class EOEPricingController(ABMController):
    """
    Equation of Exchange (EOE) pricing model.

    Price = TransactionVolume / (CirculatingSupply * Velocity)

    Where:
    - TransactionVolume = total fiat value of transactions (demand)
    - Velocity = 12 / holding_time (annualized turnover)

    Adapted from TokenLab's PriceFunction_EOE.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize EOE pricing controller.

        Config keys:
            holding_time: Average holding time in months (default: 6)
            smoothing_factor: Smoothing coefficient (0-1, default: 0.7)
            min_price: Price floor (default: 0.01)
        """
        super().__init__(config)
        self.holding_time = config.get("holding_time", 6.0)
        self.smoothing_factor = config.get("smoothing_factor", 0.7)
        self.min_price = config.get("min_price", 0.01)

        # Velocity = 12 / holding_time (annualized)
        self.velocity = 12.0 / self.holding_time

        # Optional external volume controller
        self.volume_controller = None

        logger.info(
            f"EOEPricing initialized: "
            f"holding_time={self.holding_time}m, "
            f"velocity={self.velocity:.2f}, "
            f"smoothing={self.smoothing_factor:.2f}"
        )

    def set_volume_controller(self, volume_controller):
        """
        Set external volume controller for dynamic volume calculations.

        Args:
            volume_controller: VolumeController instance
        """
        self.volume_controller = volume_controller
        logger.info("EOEPricing: External volume controller linked")

    async def execute(self) -> float:
        """
        Calculate price for current iteration.

        Returns:
            New price
        """
        token_economy = self.get_dependency(TokenEconomy)

        # Transaction volume in fiat (demand side)
        # If external volume controller exists, use it
        # Otherwise, approximate as: sell_pressure * current_price
        if self.volume_controller:
            transaction_volume_tokens = await self.volume_controller.execute()
            demand_fiat = transaction_volume_tokens * token_economy.price
            logger.debug(f"Using external volume: {transaction_volume_tokens:,.0f} tokens")
        else:
            demand_fiat = token_economy.total_sell_pressure * token_economy.price
            logger.debug(f"Using sell pressure for volume: {token_economy.total_sell_pressure:,.0f}")

        # Circulating supply
        supply = token_economy.circulating_supply

        # Calculate new price using EOE: P = Demand / (Supply * Velocity)
        if supply > 0 and self.velocity > 0:
            raw_price = demand_fiat / (supply * self.velocity)
        else:
            raw_price = token_economy.price

        # Apply smoothing to prevent wild swings
        # new_price = smoothing * old_price + (1 - smoothing) * raw_price
        smoothed_price = (
            self.smoothing_factor * token_economy.price +
            (1 - self.smoothing_factor) * raw_price
        )

        # Apply floor
        final_price = max(self.min_price, smoothed_price)

        logger.debug(
            f"EOE pricing: demand_fiat={demand_fiat:,.0f}, "
            f"supply={supply:,.0f}, raw_price=${raw_price:.4f}, "
            f"smoothed_price=${final_price:.4f}"
        )

        return final_price


class BondingCurvePricingController(ABMController):
    """
    Bonding curve pricing model.

    P = k * S^n

    Where:
    - k = price coefficient
    - S = circulating supply
    - n = curve exponent (typically 2 for quadratic)

    Adapted from TokenLab's PriceFunction_BondingCurve.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize bonding curve pricing controller.

        Config keys:
            initial_price: Price at initial supply (default: 1.0)
            initial_supply: Initial circulating supply (default: 1000000)
            curve_exponent: Exponent n (default: 2.0)
            min_price: Price floor (default: 0.01)
        """
        super().__init__(config)
        self.initial_price = config.get("initial_price", 1.0)
        self.initial_supply = config.get("initial_supply", 1000000.0)
        self.curve_exponent = config.get("curve_exponent", 2.0)
        self.min_price = config.get("min_price", 0.01)

        # Calculate k from initial conditions: k = P0 / S0^n
        if self.initial_supply > 0:
            self.k = self.initial_price / (self.initial_supply ** self.curve_exponent)
        else:
            self.k = self.initial_price

        logger.info(
            f"BondingCurve pricing initialized: "
            f"k={self.k:.2e}, exponent={self.curve_exponent}, "
            f"P0=${self.initial_price:.4f}, S0={self.initial_supply:,.0f}"
        )

    async def execute(self) -> float:
        """
        Calculate price for current iteration.

        Returns:
            New price
        """
        token_economy = self.get_dependency(TokenEconomy)

        supply = token_economy.circulating_supply

        # P = k * S^n
        if supply > 0:
            price = self.k * (supply ** self.curve_exponent)
        else:
            price = self.min_price

        # Apply floor
        final_price = max(self.min_price, price)

        logger.debug(
            f"BondingCurve pricing: supply={supply:,.0f}, "
            f"price=${final_price:.4f}"
        )

        return final_price


class IssuanceCurvePricingController(ABMController):
    """
    Issuance curve pricing model with scarcity premium.

    P = P0 * (1 + S/S_max)^alpha

    Price increases as more supply is issued (scarcity premium).

    Adapted from TokenLab's PriceFunction_IssuanceCurve.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize issuance curve pricing controller.

        Config keys:
            initial_price: Price at S=0 (default: 1.0)
            max_supply: Maximum supply (default: total supply)
            alpha: Scarcity exponent (default: 0.5)
            min_price: Price floor (default: 0.01)
        """
        super().__init__(config)
        self.initial_price = config.get("initial_price", 1.0)
        self.max_supply = config.get("max_supply", 1000000000.0)
        self.alpha = config.get("alpha", 0.5)
        self.min_price = config.get("min_price", 0.01)

        logger.info(
            f"IssuanceCurve pricing initialized: "
            f"P0=${self.initial_price:.4f}, "
            f"S_max={self.max_supply:,.0f}, "
            f"alpha={self.alpha:.2f}"
        )

    async def execute(self) -> float:
        """
        Calculate price for current iteration.

        Returns:
            New price
        """
        token_economy = self.get_dependency(TokenEconomy)

        supply = token_economy.circulating_supply

        # P = P0 * (1 + S/S_max)^alpha
        if self.max_supply > 0:
            price = self.initial_price * ((1 + supply / self.max_supply) ** self.alpha)
        else:
            price = self.initial_price

        # Apply floor
        final_price = max(self.min_price, price)

        logger.debug(
            f"IssuanceCurve pricing: supply={supply:,.0f}, "
            f"ratio={supply/self.max_supply:.4f}, "
            f"price=${final_price:.4f}"
        )

        return final_price


class ConstantPricingController(ABMController):
    """Constant (fixed) price model."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize constant pricing controller.

        Config keys:
            price: Fixed price (default: 1.0)
        """
        super().__init__(config)
        self.price = config.get("price", 1.0)

        logger.info(f"ConstantPricing initialized: price=${self.price:.4f}")

    async def execute(self) -> float:
        """Return constant price."""
        return self.price


def create_pricing_controller(
    pricing_model: PricingModel,
    config: Dict[str, Any] = None
) -> ABMController:
    """
    Factory function to create pricing controller.

    Args:
        pricing_model: Type of pricing model
        config: Configuration dict

    Returns:
        Pricing controller instance

    Raises:
        ValueError: If invalid pricing model
    """
    config = config or {}

    if pricing_model == PricingModel.EOE:
        return EOEPricingController(config)
    elif pricing_model == PricingModel.BONDING_CURVE:
        return BondingCurvePricingController(config)
    elif pricing_model == PricingModel.ISSUANCE_CURVE:
        return IssuanceCurvePricingController(config)
    elif pricing_model == PricingModel.CONSTANT:
        return ConstantPricingController(config)
    else:
        raise ValueError(f"Unknown pricing model: {pricing_model}")
