"""
TokenLab Vesting & Allocation Simulator

A comprehensive vesting schedule simulator that models token unlock patterns
and expected market sell pressure. Supports three tiers of complexity:

- Tier 1: Deterministic vesting with configurable behaviors
- Tier 2: Dynamic TokenLab integration (price-supply feedback, staking, treasury)
- Tier 3: Monte Carlo analysis and cohort-based modeling

Author: TokenLab Contributors
License: MIT
"""

import copy
import json
import warnings
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
from dateutil.relativedelta import relativedelta


# =============================================================================
# CONFIGURATION SCHEMA & CONSTANTS
# =============================================================================

SELL_PRESSURE_LEVELS = {
    "low": 0.10,
    "medium": 0.25,
    "high": 0.50
}

DEFAULT_CONFIG = {
    "token": {
        "name": "TokenA",
        "total_supply": 1_000_000_000,
        "start_date": "2026-01-01",
        "horizon_months": 36,
        "allocation_mode": "percent"  # "percent" or "tokens"
    },
    "assumptions": {
        "sell_pressure_level": "medium",  # "low", "medium", "high"
        "avg_daily_volume_tokens": None  # Optional: for sell/volume ratio
    },
    "behaviors": {
        "cliff_shock": {
            "enabled": False,
            "multiplier": 3.0,
            "buckets": []  # List of bucket names to apply shock to
        },
        "price_trigger": {
            "enabled": False,
            "source": "flat",  # "flat", "scenario", "csv"
            "scenario": None,  # "uptrend", "downtrend", "volatile"
            "take_profit": 0.5,  # +50%
            "stop_loss": -0.3,  # -30%
            "extra_sell_addon": 0.2,  # +20% sell pressure when triggered
            "uploaded_price_series": None  # List[(month_index, price)]
        },
        "relock": {
            "enabled": False,
            "relock_pct": 0.3,  # 30% of unlocks are relocked
            "lock_duration_months": 6
        }
    },
    "buckets": [
        {
            "bucket": "Team",
            "allocation": 20,  # Interpreted based on allocation_mode
            "tge_unlock_pct": 0,
            "cliff_months": 12,
            "vesting_months": 36,
            "unlock_type": "linear"  # Future-proofing
        }
    ]
}


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_config(config: Dict) -> List[str]:
    """
    Validate configuration and return list of warnings.

    Raises ValueError for critical errors that prevent simulation.
    Returns list of warning messages for non-critical issues.

    Args:
        config: Configuration dictionary

    Returns:
        List of warning messages (empty if no warnings)

    Raises:
        ValueError: If configuration has critical errors
    """
    warnings_list = []

    # Validate token section
    if "token" not in config:
        raise ValueError("Missing 'token' section in config")

    token_config = config["token"]

    if token_config.get("total_supply", 0) <= 0:
        raise ValueError("total_supply must be positive")

    if token_config.get("horizon_months", 0) <= 0:
        raise ValueError("horizon_months must be positive")

    # Validate start date format
    try:
        datetime.strptime(token_config["start_date"], "%Y-%m-%d")
    except (ValueError, KeyError):
        raise ValueError("start_date must be in YYYY-MM-DD format")

    allocation_mode = token_config.get("allocation_mode", "percent")
    if allocation_mode not in ["percent", "tokens"]:
        raise ValueError("allocation_mode must be 'percent' or 'tokens'")

    # Validate buckets
    if "buckets" not in config or not config["buckets"]:
        raise ValueError("At least one bucket must be defined")

    total_supply = token_config["total_supply"]
    allocation_sum = 0

    for i, bucket in enumerate(config["buckets"]):
        # Check required fields
        required_fields = ["bucket", "allocation", "tge_unlock_pct", "cliff_months", "vesting_months"]
        for field in required_fields:
            if field not in bucket:
                raise ValueError(f"Bucket {i}: Missing required field '{field}'")

        # Validate ranges
        if bucket["allocation"] < 0:
            raise ValueError(f"Bucket '{bucket['bucket']}': allocation cannot be negative")

        if not (0 <= bucket["tge_unlock_pct"] <= 100):
            raise ValueError(f"Bucket '{bucket['bucket']}': tge_unlock_pct must be between 0 and 100")

        if bucket["cliff_months"] < 0:
            raise ValueError(f"Bucket '{bucket['bucket']}': cliff_months cannot be negative")

        if bucket["vesting_months"] < 0:
            raise ValueError(f"Bucket '{bucket['bucket']}': vesting_months cannot be negative")

        # Calculate allocation sum
        if allocation_mode == "percent":
            allocation_sum += bucket["allocation"]
        else:  # tokens
            allocation_sum += bucket["allocation"]

    # Check allocation sum
    if allocation_mode == "percent":
        if abs(allocation_sum - 100) > 0.01:  # Allow small floating point error
            if allocation_sum > 100:
                raise ValueError(f"Allocation sum ({allocation_sum}%) exceeds 100%")
            else:
                warnings_list.append(f"Allocation sum is {allocation_sum:.2f}%, leaving {100 - allocation_sum:.2f}% unallocated")
    else:  # tokens
        if allocation_sum > total_supply:
            raise ValueError(f"Allocation sum ({allocation_sum:,.0f}) exceeds total supply ({total_supply:,.0f})")
        elif allocation_sum < total_supply:
            unallocated = total_supply - allocation_sum
            warnings_list.append(f"{unallocated:,.0f} tokens ({unallocated/total_supply*100:.2f}%) remain unallocated")

    # Validate assumptions
    if "assumptions" in config:
        assumptions = config["assumptions"]
        sell_pressure = assumptions.get("sell_pressure_level", "medium")
        if sell_pressure not in SELL_PRESSURE_LEVELS:
            raise ValueError(f"sell_pressure_level must be one of: {list(SELL_PRESSURE_LEVELS.keys())}")

        avg_volume = assumptions.get("avg_daily_volume_tokens")
        if avg_volume is not None and avg_volume < 0:
            raise ValueError("avg_daily_volume_tokens cannot be negative")

    # Validate behaviors
    if "behaviors" in config:
        behaviors = config["behaviors"]

        # Cliff shock validation
        if behaviors.get("cliff_shock", {}).get("enabled", False):
            cliff_shock = behaviors["cliff_shock"]
            if cliff_shock.get("multiplier", 1.0) < 1.0:
                raise ValueError("cliff_shock multiplier must be >= 1.0")

            # Check if specified buckets exist
            bucket_names = {b["bucket"] for b in config["buckets"]}
            for shock_bucket in cliff_shock.get("buckets", []):
                if shock_bucket not in bucket_names:
                    warnings_list.append(f"Cliff shock bucket '{shock_bucket}' not found in bucket list")

        # Price trigger validation
        if behaviors.get("price_trigger", {}).get("enabled", False):
            price_trigger = behaviors["price_trigger"]
            source = price_trigger.get("source", "flat")

            if source not in ["flat", "scenario", "csv"]:
                raise ValueError("price_trigger source must be 'flat', 'scenario', or 'csv'")

            if source == "scenario":
                scenario = price_trigger.get("scenario")
                if scenario not in ["uptrend", "downtrend", "volatile"]:
                    raise ValueError("price_trigger scenario must be 'uptrend', 'downtrend', or 'volatile'")

            if source == "csv":
                if not price_trigger.get("uploaded_price_series"):
                    raise ValueError("price_trigger source is 'csv' but no uploaded_price_series provided")

        # Relock validation
        if behaviors.get("relock", {}).get("enabled", False):
            relock = behaviors["relock"]
            relock_pct = relock.get("relock_pct", 0)
            if not (0 <= relock_pct <= 1.0):
                raise ValueError("relock_pct must be between 0 and 1.0")

            if relock.get("lock_duration_months", 0) < 0:
                raise ValueError("lock_duration_months cannot be negative")

    return warnings_list


def normalize_config(config: Dict) -> Dict:
    """
    Normalize and enrich configuration with computed fields.

    Args:
        config: Raw configuration dictionary

    Returns:
        Normalized configuration with added computed fields
    """
    normalized = copy.deepcopy(config)

    # Convert allocations to tokens
    allocation_mode = normalized["token"]["allocation_mode"]
    total_supply = normalized["token"]["total_supply"]

    for bucket in normalized["buckets"]:
        if allocation_mode == "percent":
            bucket["allocation_tokens"] = total_supply * (bucket["allocation"] / 100.0)
        else:
            bucket["allocation_tokens"] = bucket["allocation"]

    return normalized


# =============================================================================
# VESTING BUCKET CONTROLLER
# =============================================================================

class VestingBucketController:
    """
    Controller for a single vesting bucket.

    Manages state and calculations for one allocation bucket, including:
    - Baseline vesting schedule (cliff + linear)
    - Relock/staking delays
    - Sell pressure calculation
    - Historical tracking
    """

    def __init__(self, bucket_config: Dict, global_config: Dict):
        """
        Initialize bucket controller.

        Args:
            bucket_config: Configuration for this specific bucket
            global_config: Global configuration (for assumptions, behaviors)
        """
        self.config = bucket_config
        self.global_config = global_config
        self.iteration = 0

        # State tracking
        self.allocation_tokens = bucket_config["allocation_tokens"]
        self.unlocked_cumulative = 0.0
        self.locked_remaining = self.allocation_tokens

        # Relock schedule: {month_index: amount_to_mature}
        self.relock_schedule = {}

        # Historical stores
        self._unlocked_store = []
        self._locked_store = []
        self._relock_this_month_store = []
        self._matured_relock_store = []
        self._sell_pressure_store = []
        self._expected_sell_store = []
        self._expected_circulating_cumulative_store = []

        self.expected_circulating_cumulative = 0.0

    def execute(self, month_index: int, current_price: float, initial_price: float) -> float:
        """
        Execute one month of vesting for this bucket.

        Args:
            month_index: Current month (0 = TGE)
            current_price: Current token price (for price triggers)
            initial_price: Initial TGE price (for price change calculation)

        Returns:
            Amount unlocked this month
        """
        # Calculate baseline unlock
        unlocked_this_month = self._calculate_baseline_unlock(month_index)

        # Apply relock (only to post-cliff vesting, not TGE)
        # Decision: Relock applies only to linear vesting unlocks (Question 2: Option B)
        if month_index > 0:  # Not TGE
            free_unlocked, relocked_amount = self._apply_relock(unlocked_this_month, month_index)
        else:
            free_unlocked = unlocked_this_month
            relocked_amount = 0.0

        # Get matured relock from previous months
        matured_relock = self._calculate_matured_relock(month_index)

        # Calculate sell pressure
        sell_pressure = self._calculate_sell_pressure(month_index, current_price, initial_price)

        # Calculate expected sell
        available_to_sell = free_unlocked + matured_relock
        expected_sell_this_month = available_to_sell * sell_pressure

        # Update cumulative state
        self.unlocked_cumulative += unlocked_this_month
        self.locked_remaining = max(0.0, self.allocation_tokens - self.unlocked_cumulative)
        self.expected_circulating_cumulative += expected_sell_this_month

        # Store history
        self._unlocked_store.append(unlocked_this_month)
        self._locked_store.append(self.locked_remaining)
        self._relock_this_month_store.append(relocked_amount)
        self._matured_relock_store.append(matured_relock)
        self._sell_pressure_store.append(sell_pressure)
        self._expected_sell_store.append(expected_sell_this_month)
        self._expected_circulating_cumulative_store.append(self.expected_circulating_cumulative)

        self.iteration += 1
        return unlocked_this_month

    def _calculate_baseline_unlock(self, month_index: int) -> float:
        """
        Calculate baseline vesting unlock for this month.

        Implements cliff + linear vesting schedule.

        Args:
            month_index: Current month (0 = TGE)

        Returns:
            Amount unlocked this month
        """
        allocation = self.config["allocation_tokens"]
        tge_pct = self.config["tge_unlock_pct"]
        cliff_months = self.config["cliff_months"]
        vesting_months = self.config["vesting_months"]

        # Month 0: TGE unlock
        if month_index == 0:
            tge_unlock = allocation * (tge_pct / 100.0)
            return tge_unlock

        # Calculate locked amount after TGE
        locked_initial = allocation * (1 - tge_pct / 100.0)

        # During cliff: no unlocks
        if month_index <= cliff_months:
            return 0.0

        # After cliff: check if we're in vesting period
        if vesting_months == 0:
            # Edge case: no vesting period, all unlocks at cliff end
            if month_index == cliff_months + 1:
                return locked_initial
            else:
                return 0.0

        # Linear vesting period
        if month_index <= cliff_months + vesting_months:
            monthly_chunk = locked_initial / vesting_months
            return monthly_chunk

        # After vesting complete: no more unlocks
        return 0.0

    def _apply_relock(self, unlocked_amount: float, month_index: int) -> Tuple[float, float]:
        """
        Apply relock mechanism to unlocked tokens.

        Decision: Relock only applies to post-cliff linear vesting (Question 2: Option B)

        Args:
            unlocked_amount: Amount unlocked this month
            month_index: Current month

        Returns:
            Tuple of (free_amount, relocked_amount)
        """
        relock_config = self.global_config["behaviors"].get("relock", {})

        if not relock_config.get("enabled", False):
            return unlocked_amount, 0.0

        relock_pct = relock_config["relock_pct"]
        lock_duration = relock_config["lock_duration_months"]

        # Calculate relock amount
        relock_amount = unlocked_amount * relock_pct
        free_amount = unlocked_amount - relock_amount

        # Schedule maturity
        maturity_month = month_index + lock_duration
        if maturity_month not in self.relock_schedule:
            self.relock_schedule[maturity_month] = 0.0
        self.relock_schedule[maturity_month] += relock_amount

        return free_amount, relock_amount

    def _calculate_matured_relock(self, month_index: int) -> float:
        """
        Get relocked tokens maturing this month.

        Args:
            month_index: Current month

        Returns:
            Amount of relocked tokens maturing
        """
        matured = self.relock_schedule.get(month_index, 0.0)
        if matured > 0:
            del self.relock_schedule[month_index]
        return matured

    def _calculate_sell_pressure(self, month_index: int, current_price: float, initial_price: float) -> float:
        """
        Calculate effective sell pressure for this month.

        Applies precedence: base -> price trigger -> cliff shock
        (PRD §8: Question 4: Price baseline is TGE fixed)

        Args:
            month_index: Current month
            current_price: Current token price
            initial_price: TGE price

        Returns:
            Effective sell pressure (0 to 1.0)
        """
        # Step 1: Base sell pressure
        sell_pressure_level = self.global_config["assumptions"]["sell_pressure_level"]
        S_base = SELL_PRESSURE_LEVELS[sell_pressure_level]

        # Step 2: Apply price trigger addon (if enabled)
        S1 = S_base
        price_trigger_config = self.global_config["behaviors"].get("price_trigger", {})
        if price_trigger_config.get("enabled", False):
            price_change = (current_price / initial_price) - 1.0
            take_profit = price_trigger_config["take_profit"]
            stop_loss = price_trigger_config["stop_loss"]
            extra_addon = price_trigger_config["extra_sell_addon"]

            if price_change >= take_profit or price_change <= stop_loss:
                S1 = min(1.0, S_base + extra_addon)

        # Step 3: Apply cliff shock multiplier (if applicable)
        # Decision: Cliff shock only applies if cliff > 0 (Question 3: Option A)
        S_effective = S1
        cliff_shock_config = self.global_config["behaviors"].get("cliff_shock", {})
        if cliff_shock_config.get("enabled", False):
            cliff_months = self.config["cliff_months"]

            # First vest month after cliff (only if cliff > 0)
            if cliff_months > 0 and month_index == cliff_months + 1:
                # Check if this bucket is in the shock list
                bucket_name = self.config["bucket"]
                if bucket_name in cliff_shock_config.get("buckets", []):
                    multiplier = cliff_shock_config["multiplier"]
                    S_effective = min(1.0, S1 * multiplier)

        return S_effective

    def get_history(self) -> Dict[str, List[float]]:
        """
        Get historical tracking data.

        Returns:
            Dictionary of historical arrays
        """
        return {
            "unlocked_this_month": self._unlocked_store,
            "locked_remaining": self._locked_store,
            "relock_this_month": self._relock_this_month_store,
            "matured_relock": self._matured_relock_store,
            "sell_pressure": self._sell_pressure_store,
            "expected_sell_this_month": self._expected_sell_store,
            "expected_circulating_cumulative": self._expected_circulating_cumulative_store
        }

    def reset(self):
        """Reset controller state for Monte Carlo trials."""
        self.iteration = 0
        self.unlocked_cumulative = 0.0
        self.locked_remaining = self.allocation_tokens
        self.relock_schedule = {}
        self.expected_circulating_cumulative = 0.0

        self._unlocked_store = []
        self._locked_store = []
        self._relock_this_month_store = []
        self._matured_relock_store = []
        self._sell_pressure_store = []
        self._expected_sell_store = []
        self._expected_circulating_cumulative_store = []


# =============================================================================
# VESTING SIMULATOR (MAIN ORCHESTRATOR)
# =============================================================================

class VestingSimulator:
    """
    Main orchestrator for vesting simulation.

    Manages:
    - Configuration validation
    - Bucket controller initialization
    - Simulation execution
    - Data aggregation
    - Chart generation
    - Export functionality
    """

    def __init__(self, config: Dict, mode: str = "tier1"):
        """
        Initialize vesting simulator.

        Args:
            config: Configuration dictionary
            mode: Simulation mode - "tier1", "tier2", or "tier3"
        """
        # Validate configuration
        self.warnings = validate_config(config)

        # Normalize configuration
        self.config = normalize_config(config)
        self.mode = mode

        # Initialize bucket controllers
        self.bucket_controllers = []
        for bucket_config in self.config["buckets"]:
            controller = VestingBucketController(bucket_config, self.config)
            self.bucket_controllers.append(controller)

        # Price series (for price triggers)
        self.price_series = None
        self.initial_price = 1.0  # Default TGE price

        # Results storage
        self.df_bucket_long = None
        self.df_global = None
        self.summary_cards = None

    def run_simulation(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Run the vesting simulation.

        Returns:
            Tuple of (df_bucket_long, df_global)
        """
        # Generate price series
        self.price_series = self._generate_price_series()

        # Run monthly simulation
        horizon_months = self.config["token"]["horizon_months"]

        for month_index in range(horizon_months + 1):
            current_price = self.price_series[month_index]

            # Execute all bucket controllers
            for controller in self.bucket_controllers:
                controller.execute(month_index, current_price, self.initial_price)

        # Aggregate results
        self.df_bucket_long = self._build_bucket_dataframe()
        self.df_global = self._build_global_dataframe()
        self.summary_cards = self._calculate_summary_cards()

        return self.df_bucket_long, self.df_global

    def _generate_price_series(self) -> List[float]:
        """
        Generate price series for simulation.

        Returns:
            List of prices for each month
        """
        horizon_months = self.config["token"]["horizon_months"]
        price_trigger_config = self.config["behaviors"].get("price_trigger", {})

        if not price_trigger_config.get("enabled", False):
            # No price trigger: flat price at 1.0
            return [1.0] * (horizon_months + 1)

        source = price_trigger_config["source"]

        if source == "flat":
            return [1.0] * (horizon_months + 1)

        elif source == "scenario":
            scenario = price_trigger_config["scenario"]
            prices = []

            for m in range(horizon_months + 1):
                if scenario == "uptrend":
                    price = 1.0 * (1.05 ** m)
                elif scenario == "downtrend":
                    price = 1.0 * (0.95 ** m)
                elif scenario == "volatile":
                    price = 1.0 * (1.10 if m % 2 == 0 else 0.90)
                else:
                    price = 1.0
                prices.append(price)

            return prices

        elif source == "csv":
            uploaded_series = price_trigger_config["uploaded_price_series"]
            if not uploaded_series:
                # Fallback to flat
                return [1.0] * (horizon_months + 1)

            # Convert to dict for easy lookup
            price_dict = {month: price for month, price in uploaded_series}

            # Fill in missing months with interpolation
            prices = []
            for m in range(horizon_months + 1):
                if m in price_dict:
                    prices.append(price_dict[m])
                elif prices:
                    # Use last known price
                    prices.append(prices[-1])
                else:
                    prices.append(1.0)

            return prices

        return [1.0] * (horizon_months + 1)

    def _build_bucket_dataframe(self) -> pd.DataFrame:
        """
        Build detailed bucket-level dataframe.

        Returns:
            DataFrame with columns: month_index, date, bucket, allocation_tokens,
                                   unlocked_this_month, unlocked_cumulative, locked_remaining,
                                   sell_pressure_effective, expected_sell_this_month,
                                   expected_circulating_cumulative
        """
        records = []

        start_date = datetime.strptime(self.config["token"]["start_date"], "%Y-%m-%d")
        horizon_months = self.config["token"]["horizon_months"]

        for controller in self.bucket_controllers:
            bucket_name = controller.config["bucket"]
            history = controller.get_history()

            for month_index in range(horizon_months + 1):
                date = start_date + relativedelta(months=month_index)

                record = {
                    "month_index": month_index,
                    "date": date.strftime("%Y-%m-%d"),
                    "bucket": bucket_name,
                    "allocation_tokens": controller.allocation_tokens,
                    "unlocked_this_month": history["unlocked_this_month"][month_index],
                    "unlocked_cumulative": sum(history["unlocked_this_month"][:month_index+1]),
                    "locked_remaining": history["locked_remaining"][month_index],
                    "sell_pressure_effective": history["sell_pressure"][month_index],
                    "expected_sell_this_month": history["expected_sell_this_month"][month_index],
                    "expected_circulating_cumulative": history["expected_circulating_cumulative"][month_index]
                }
                records.append(record)

        return pd.DataFrame(records)

    def _build_global_dataframe(self) -> pd.DataFrame:
        """
        Build aggregated global metrics dataframe.

        Returns:
            DataFrame with columns: month_index, date, total_unlocked, total_expected_sell,
                                   expected_circulating_total, expected_circulating_pct,
                                   sell_volume_ratio
        """
        records = []

        start_date = datetime.strptime(self.config["token"]["start_date"], "%Y-%m-%d")
        horizon_months = self.config["token"]["horizon_months"]
        total_supply = self.config["token"]["total_supply"]
        avg_daily_volume = self.config["assumptions"].get("avg_daily_volume_tokens")

        for month_index in range(horizon_months + 1):
            date = start_date + relativedelta(months=month_index)

            # Aggregate across buckets
            total_unlocked = 0.0
            total_expected_sell = 0.0
            expected_circulating_total = 0.0

            for controller in self.bucket_controllers:
                history = controller.get_history()
                total_unlocked += history["unlocked_this_month"][month_index]
                total_expected_sell += history["expected_sell_this_month"][month_index]
                expected_circulating_total += history["expected_circulating_cumulative"][month_index]

            expected_circulating_pct = expected_circulating_total / total_supply

            # Calculate sell/volume ratio if volume provided
            sell_volume_ratio = None
            if avg_daily_volume is not None and avg_daily_volume > 0:
                monthly_volume = avg_daily_volume * 30
                sell_volume_ratio = total_expected_sell / monthly_volume if monthly_volume > 0 else 0

            record = {
                "month_index": month_index,
                "date": date.strftime("%Y-%m-%d"),
                "total_unlocked": total_unlocked,
                "total_expected_sell": total_expected_sell,
                "expected_circulating_total": expected_circulating_total,
                "expected_circulating_pct": expected_circulating_pct,
                "sell_volume_ratio": sell_volume_ratio
            }
            records.append(record)

        return pd.DataFrame(records)

    def _calculate_summary_cards(self) -> Dict[str, Any]:
        """
        Calculate summary statistics for display.

        Returns:
            Dictionary with summary metrics
        """
        df = self.df_global
        total_supply = self.config["token"]["total_supply"]
        horizon_months = self.config["token"]["horizon_months"]

        # Max monthly unlock
        max_unlock_idx = df["total_unlocked"].idxmax()
        max_unlock_tokens = df.loc[max_unlock_idx, "total_unlocked"]
        max_unlock_month = df.loc[max_unlock_idx, "month_index"]

        # Max monthly sell
        max_sell_idx = df["total_expected_sell"].idxmax()
        max_sell_tokens = df.loc[max_sell_idx, "total_expected_sell"]
        max_sell_month = df.loc[max_sell_idx, "month_index"]

        # Circulating percentages at key milestones
        circ_12_pct = df.loc[df["month_index"] == 12, "expected_circulating_pct"].values[0] * 100 if len(df[df["month_index"] == 12]) > 0 else None
        circ_24_pct = df.loc[df["month_index"] == 24, "expected_circulating_pct"].values[0] * 100 if len(df[df["month_index"] == 24]) > 0 else None
        circ_end_pct = df.iloc[-1]["expected_circulating_pct"] * 100

        return {
            "max_unlock_tokens": max_unlock_tokens,
            "max_unlock_month": int(max_unlock_month),
            "max_sell_tokens": max_sell_tokens,
            "max_sell_month": int(max_sell_month),
            "circ_12_pct": circ_12_pct,
            "circ_24_pct": circ_24_pct,
            "circ_end_pct": circ_end_pct
        }

    def make_charts(self, df_bucket_long: pd.DataFrame = None, df_global: pd.DataFrame = None) -> List[plt.Figure]:
        """
        Generate visualization charts.

        Args:
            df_bucket_long: Bucket-level dataframe (uses self.df_bucket_long if None)
            df_global: Global dataframe (uses self.df_global if None)

        Returns:
            List of matplotlib Figure objects
        """
        if df_bucket_long is None:
            df_bucket_long = self.df_bucket_long
        if df_global is None:
            df_global = self.df_global

        figs = []

        # Chart 1: Stacked bar - Unlocks by bucket
        fig1 = self._create_unlock_chart(df_bucket_long)
        figs.append(fig1)

        # Chart 2: Line - Circulating supply
        fig2 = self._create_circulating_chart(df_global)
        figs.append(fig2)

        # Chart 3: Bar - Sell flow
        fig3 = self._create_sell_flow_chart(df_global)
        figs.append(fig3)

        return figs

    def _create_unlock_chart(self, df_bucket_long: pd.DataFrame) -> plt.Figure:
        """Create stacked bar chart of unlocks by bucket."""
        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)

        # Pivot for stacking
        pivot = df_bucket_long.pivot(index="month_index", columns="bucket", values="unlocked_this_month")

        # Stacked bar
        pivot.plot(kind="bar", stacked=True, ax=ax, width=0.8,
                   colormap="tab20", edgecolor="white", linewidth=0.5)

        ax.set_xlabel("Month", fontsize=12, fontweight="bold")
        ax.set_ylabel("Tokens Unlocked", fontsize=12, fontweight="bold")
        ax.set_title("Monthly Unlock Schedule by Bucket", fontsize=14, fontweight="bold", pad=20)
        ax.legend(title="Bucket", bbox_to_anchor=(1.05, 1), loc="upper left")
        ax.grid(axis="y", alpha=0.3, linestyle="--")

        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x/1e6:.0f}M" if x >= 1e6 else f"{x/1e3:.0f}K"))

        plt.tight_layout()
        return fig

    def _create_circulating_chart(self, df_global: pd.DataFrame) -> plt.Figure:
        """Create line chart of circulating supply with dual y-axis."""
        fig, ax1 = plt.subplots(figsize=(12, 6), dpi=100)

        # Left y-axis: Absolute tokens
        color1 = "#2E86AB"
        ax1.plot(df_global["month_index"], df_global["expected_circulating_total"],
                 color=color1, linewidth=2.5, label="Circulating Tokens")
        ax1.fill_between(df_global["month_index"], 0, df_global["expected_circulating_total"],
                         alpha=0.2, color=color1)
        ax1.set_xlabel("Month", fontsize=12, fontweight="bold")
        ax1.set_ylabel("Circulating Supply (Tokens)", fontsize=12, fontweight="bold", color=color1)
        ax1.tick_params(axis="y", labelcolor=color1)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x/1e6:.0f}M" if x >= 1e6 else f"{x/1e3:.0f}K"))

        # Right y-axis: Percentage
        ax2 = ax1.twinx()
        color2 = "#A23B72"
        ax2.plot(df_global["month_index"], df_global["expected_circulating_pct"] * 100,
                 color=color2, linewidth=2, linestyle="--", label="% of Supply")
        ax2.set_ylabel("% of Total Supply", fontsize=12, fontweight="bold", color=color2)
        ax2.tick_params(axis="y", labelcolor=color2)
        ax2.set_ylim(0, 100)

        ax1.set_title("Expected Circulating Supply Over Time", fontsize=14, fontweight="bold", pad=20)
        ax1.grid(axis="both", alpha=0.3, linestyle="--")

        # Combined legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

        plt.tight_layout()
        return fig

    def _create_sell_flow_chart(self, df_global: pd.DataFrame) -> plt.Figure:
        """Create bar chart of expected sell flow."""
        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)

        ax.bar(df_global["month_index"], df_global["total_expected_sell"],
               color="#F18F01", alpha=0.7, edgecolor="black", linewidth=0.5)

        ax.set_xlabel("Month", fontsize=12, fontweight="bold")
        ax.set_ylabel("Expected Sell Volume", fontsize=12, fontweight="bold")
        ax.set_title("Expected Monthly Sell Pressure", fontsize=14, fontweight="bold", pad=20)
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x/1e6:.0f}M" if x >= 1e6 else f"{x/1e3:.0f}K"))

        plt.tight_layout()
        return fig

    def export_csvs(self, output_dir: str) -> Tuple[str, str]:
        """
        Export dataframes to CSV files.

        Args:
            output_dir: Directory to save CSV files

        Returns:
            Tuple of (bucket_csv_path, global_csv_path)
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        bucket_path = os.path.join(output_dir, "vesting_bucket_schedule.csv")
        global_path = os.path.join(output_dir, "vesting_global_metrics.csv")

        self.df_bucket_long.to_csv(bucket_path, index=False)
        self.df_global.to_csv(global_path, index=False)

        return bucket_path, global_path

    def export_pdf(self, output_path: str) -> str:
        """
        Export summary report as PDF.

        Args:
            output_path: Path to save PDF file

        Returns:
            Path to saved PDF
        """
        figs = self.make_charts()

        with PdfPages(output_path) as pdf:
            # Page 1: Summary
            fig_summary = plt.figure(figsize=(11, 8.5))
            fig_summary.text(0.5, 0.95, "TokenLab Vesting Analysis Report",
                            ha="center", fontsize=18, fontweight="bold")
            fig_summary.text(0.5, 0.92, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                            ha="center", fontsize=10, color="gray")

            # Summary text
            token_name = self.config["token"].get("name", "Token")
            total_supply = self.config["token"]["total_supply"]
            horizon = self.config["token"]["horizon_months"]

            summary_text = f"""
Project: {token_name}
Total Supply: {total_supply:,.0f}
Horizon: {horizon} months

Key Metrics:
• Max Monthly Unlock: {self.summary_cards['max_unlock_tokens']:,.0f} tokens in Month {self.summary_cards['max_unlock_month']}
• Max Monthly Sell: {self.summary_cards['max_sell_tokens']:,.0f} tokens in Month {self.summary_cards['max_sell_month']}
• Circulating at Month 12: {self.summary_cards['circ_12_pct']:.1f}% (if available)
• Circulating at Month 24: {self.summary_cards['circ_24_pct']:.1f}% (if available)
• Circulating at End: {self.summary_cards['circ_end_pct']:.1f}%
            """

            fig_summary.text(0.1, 0.75, summary_text, fontsize=11, verticalalignment="top",
                            family="monospace", bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3))

            pdf.savefig(fig_summary, bbox_inches="tight")
            plt.close(fig_summary)

            # Pages 2-4: Charts
            for fig in figs:
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)

            # Metadata
            d = pdf.infodict()
            d["Title"] = "TokenLab Vesting Analysis"
            d["Author"] = "TokenLab Vesting Simulator"
            d["Subject"] = "Token unlock and sell pressure analysis"
            d["Keywords"] = "tokenomics, vesting, unlock schedule"

        return output_path

    def to_json(self) -> str:
        """
        Export configuration as JSON string.

        Returns:
            JSON string of configuration
        """
        return json.dumps(self.config, indent=2)

    @staticmethod
    def from_json(json_str: str) -> "VestingSimulator":
        """
        Create simulator from JSON configuration.

        Args:
            json_str: JSON string of configuration

        Returns:
            VestingSimulator instance
        """
        config = json.loads(json_str)
        return VestingSimulator(config)
