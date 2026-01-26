"""
Treasury Controller - Fee collection, liquidity, and buyback.

Adapted from TokenLab's TreasuryBasic with enhancements:
- Transaction fee collection
- Liquidity deployment
- Token buyback and burn
- Treasury balance tracking
"""
from dataclasses import dataclass
from typing import Dict, Any
import logging

from app.abm.core.controller import ABMController
from app.abm.dynamics.token_economy import TokenEconomy

logger = logging.getLogger(__name__)


@dataclass
class TreasuryConfig:
    """Treasury configuration."""
    # Initial allocation
    initial_balance_pct: float = 0.15  # 15% of total supply

    # Fee collection
    transaction_fee_pct: float = 0.02  # 2% fee on sales

    # Allocation strategy (must sum to 1.0)
    hold_pct: float = 0.50  # 50% hold as reserves
    liquidity_pct: float = 0.30  # 30% deploy to liquidity
    buyback_pct: float = 0.20  # 20% buyback tokens

    # Buyback behavior
    burn_bought_tokens: bool = True  # Burn tokens after buyback (deflationary)


class TreasuryController(ABMController):
    """
    Treasury management system.

    Features:
    - Collects transaction fees (% of sell volume)
    - Manages fiat and token balances
    - Deploys liquidity (provides market depth)
    - Executes buybacks (removes tokens from circulation)
    - Optional token burning (deflationary pressure)
    """

    def __init__(self, config: TreasuryConfig, total_supply: float):
        """
        Initialize treasury controller.

        Args:
            config: Treasury configuration
            total_supply: Total token supply
        """
        super().__init__(config)
        self.config = config

        # Initial balances
        self.token_balance = total_supply * config.initial_balance_pct
        self.fiat_balance = 0.0

        # Liquidity deployed (tracked separately)
        self.liquidity_deployed_tokens = 0.0
        self.liquidity_deployed_fiat = 0.0

        # Cumulative metrics
        self.total_fees_collected = 0.0
        self.total_tokens_bought = 0.0
        self.total_tokens_burned = 0.0

        logger.info(
            f"TreasuryController initialized: "
            f"initial_tokens={self.token_balance:,.0f}, "
            f"fee={config.transaction_fee_pct:.1%}, "
            f"strategy=(hold={config.hold_pct:.0%}, "
            f"liq={config.liquidity_pct:.0%}, "
            f"buyback={config.buyback_pct:.0%})"
        )

        # Validate allocation percentages
        total_pct = config.hold_pct + config.liquidity_pct + config.buyback_pct
        if abs(total_pct - 1.0) > 0.01:
            raise ValueError(
                f"Treasury allocation percentages must sum to 1.0, got {total_pct:.2f}"
            )

    async def execute(
        self,
        sell_volume_tokens: float = 0.0,
        current_price: float = 1.0
    ) -> Dict[str, float]:
        """
        Execute one treasury iteration.

        1. Collect transaction fees
        2. Allocate fees (hold/liquidity/buyback)
        3. Execute buyback
        4. Update token economy

        Args:
            sell_volume_tokens: Total tokens sold this month
            current_price: Current token price

        Returns:
            Dictionary with treasury metrics
        """
        token_economy = self.get_dependency(TokenEconomy)

        # 1. Collect transaction fees (in fiat)
        fees_fiat = sell_volume_tokens * current_price * self.config.transaction_fee_pct
        self.fiat_balance += fees_fiat
        self.total_fees_collected += fees_fiat

        if fees_fiat > 0:
            logger.debug(
                f"Collected fees: ${fees_fiat:,.2f} "
                f"(from {sell_volume_tokens:,.0f} tokens sold @ ${current_price:.4f})"
            )

        # 2. Allocate fees according to strategy
        hold_amount = fees_fiat * self.config.hold_pct
        liquidity_amount = fees_fiat * self.config.liquidity_pct
        buyback_amount = fees_fiat * self.config.buyback_pct

        # 3. Deploy liquidity (add to liquidity pool)
        if liquidity_amount > 0:
            # Split 50/50 between tokens and fiat
            liquidity_fiat = liquidity_amount / 2
            liquidity_tokens = liquidity_fiat / current_price if current_price > 0 else 0

            # Use tokens from treasury balance
            if liquidity_tokens <= self.token_balance:
                self.liquidity_deployed_fiat += liquidity_fiat
                self.liquidity_deployed_tokens += liquidity_tokens
                self.token_balance -= liquidity_tokens
                self.fiat_balance -= liquidity_fiat

                logger.debug(
                    f"Deployed liquidity: {liquidity_tokens:,.0f} tokens + "
                    f"${liquidity_fiat:,.2f} fiat"
                )
            else:
                # Not enough tokens, keep as fiat
                logger.debug("Insufficient tokens for liquidity, holding as fiat")

        # 4. Execute buyback
        tokens_bought = 0.0
        tokens_burned = 0.0

        if buyback_amount > 0 and current_price > 0:
            tokens_bought = buyback_amount / current_price
            self.fiat_balance -= buyback_amount
            self.total_tokens_bought += tokens_bought

            if self.config.burn_bought_tokens:
                # Burn tokens (deflationary)
                tokens_burned = tokens_bought
                self.total_tokens_burned += tokens_burned

                # Remove from circulating supply
                token_economy.update_circulating_supply(-tokens_burned)

                logger.debug(
                    f"Buyback & burn: {tokens_bought:,.0f} tokens for "
                    f"${buyback_amount:,.2f} (BURNED)"
                )
            else:
                # Add to treasury balance
                self.token_balance += tokens_bought

                logger.debug(
                    f"Buyback: {tokens_bought:,.0f} tokens for "
                    f"${buyback_amount:,.2f} (held in treasury)"
                )

        # 5. Increment iteration
        self.iteration += 1

        return {
            "fees_collected": fees_fiat,
            "fiat_balance": self.fiat_balance,
            "token_balance": self.token_balance,
            "liquidity_deployed_fiat": self.liquidity_deployed_fiat,
            "liquidity_deployed_tokens": self.liquidity_deployed_tokens,
            "tokens_bought": tokens_bought,
            "tokens_burned": tokens_burned,
            "total_fees_collected": self.total_fees_collected,
            "total_tokens_burned": self.total_tokens_burned
        }

    def snapshot_state(self) -> Dict[str, Any]:
        """Snapshot treasury state."""
        state = super().snapshot_state()
        state.update({
            "token_balance": self.token_balance,
            "fiat_balance": self.fiat_balance,
            "liquidity_deployed_tokens": self.liquidity_deployed_tokens,
            "liquidity_deployed_fiat": self.liquidity_deployed_fiat,
            "total_fees_collected": self.total_fees_collected,
            "total_tokens_bought": self.total_tokens_bought,
            "total_tokens_burned": self.total_tokens_burned
        })
        return state

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore treasury state."""
        super().restore_state(state)
        self.token_balance = state["token_balance"]
        self.fiat_balance = state["fiat_balance"]
        self.liquidity_deployed_tokens = state["liquidity_deployed_tokens"]
        self.liquidity_deployed_fiat = state["liquidity_deployed_fiat"]
        self.total_fees_collected = state["total_fees_collected"]
        self.total_tokens_bought = state["total_tokens_bought"]
        self.total_tokens_burned = state["total_tokens_burned"]

    def __repr__(self) -> str:
        return (
            f"TreasuryController(fiat=${self.fiat_balance:,.0f}, "
            f"tokens={self.token_balance:,.0f}, "
            f"burned={self.total_tokens_burned:,.0f})"
        )
