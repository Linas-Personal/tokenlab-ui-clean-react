"""
Simulator service - wrapper around existing VestingSimulator.
"""
import sys
from pathlib import Path
from typing import Tuple, List
import pandas as pd

# Add src directory to path to import existing simulator
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from tokenlab_abm.analytics.vesting_simulator import (
    VestingSimulator,
    VestingSimulatorAdvanced,
    validate_config
)

from app.models.request import SimulationConfig
from app.models.response import BucketResult, GlobalMetric, SummaryCards, SimulationData


class SimulatorService:
    """Service class for running vesting simulations."""

    @classmethod
    def run_simulation(cls, config: SimulationConfig) -> Tuple[SimulationData, List[str]]:
        """
        Run vesting simulation.

        Args:
            config: Simulation configuration

        Returns:
            Tuple of (SimulationData, warnings)

        Raises:
            ValueError: If configuration is invalid
        """
        # Convert Pydantic model to dict using built-in method
        config_dict = config.model_dump(exclude_none=True)

        # Select simulator class based on mode
        mode = config.token.simulation_mode
        SimulatorClass = VestingSimulatorAdvanced if mode in ["tier2", "tier3"] else VestingSimulator

        # Run simulation
        simulator = SimulatorClass(config_dict, mode=mode)

        # Check if Monte Carlo is enabled (Tier 3 only)
        if mode == "tier3" and config.tier3 and config.tier3.monte_carlo and config.tier3.monte_carlo.enabled:
            num_trials = config.tier3.monte_carlo.num_trials
            df_stats, df_all_trials = simulator.run_monte_carlo(num_trials=num_trials)
            # Use aggregated statistics for the response
            df_bucket, df_global = simulator.df_bucket_long, df_stats
        else:
            df_bucket, df_global = simulator.run_simulation()

        # Convert DataFrames to Pydantic models
        # Handle different column names between Tier 1 and Tier 2/3
        bucket_results = [
            BucketResult(
                month_index=int(row["month_index"]),
                date=row["date"],
                bucket=row["bucket"],
                allocation_tokens=float(row.get("allocation_tokens") or row.get("allocation", 0)),
                unlocked_this_month=float(row["unlocked_this_month"]),
                unlocked_cumulative=float(row["unlocked_cumulative"]),
                locked_remaining=float(row["locked_remaining"]),
                sell_pressure_effective=float(row.get("sell_pressure_effective") or row.get("sell_pressure", 0)),
                expected_sell_this_month=float(row.get("expected_sell_this_month") or row.get("expected_sell", 0)),
                expected_circulating_cumulative=float(row["expected_circulating_cumulative"])
            )
            for row in df_bucket.to_dict(orient="records")
        ]

        # Handle Monte Carlo statistics (use mean values, ignore confidence bands for now)
        global_metrics = []
        for row in df_global.to_dict(orient="records"):
            # For Monte Carlo, columns are like "total_unlocked_mean", "total_unlocked_p10", etc.
            # For regular sim, columns are just "total_unlocked"
            total_unlocked = row.get("total_unlocked") or row.get("total_unlocked_mean", 0)
            total_expected_sell = row.get("total_expected_sell") or row.get("total_expected_sell_mean", 0)
            expected_circulating_total = row.get("expected_circulating_total") or row.get("expected_circulating_total_mean", 0)
            expected_circulating_pct = row.get("expected_circulating_pct") or row.get("expected_circulating_pct_mean", 0)

            global_metrics.append(
                GlobalMetric(
                    month_index=int(row["month_index"]),
                    date=row.get("date", ""),  # Monte Carlo stats don't have date
                    total_unlocked=float(total_unlocked),
                    total_expected_sell=float(total_expected_sell),
                    expected_circulating_total=float(expected_circulating_total),
                    expected_circulating_pct=float(expected_circulating_pct),
                    sell_volume_ratio=float(row["sell_volume_ratio"]) if row.get("sell_volume_ratio") is not None else None,
                    current_price=float(row["current_price"]) if row.get("current_price") is not None else None,
                    staked_amount=float(row["staked_amount"]) if row.get("staked_amount") is not None else None,
                    liquidity_deployed=float(row["liquidity_deployed"]) if row.get("liquidity_deployed") is not None else None,
                    treasury_balance=float(row["treasury_balance"]) if row.get("treasury_balance") is not None else None
                )
            )

        # Handle None values for circ_X_pct (happens when horizon < X months)
        summary_cards = SummaryCards(
            max_unlock_tokens=float(simulator.summary_cards["max_unlock_tokens"]),
            max_unlock_month=int(simulator.summary_cards["max_unlock_month"]),
            max_sell_tokens=float(simulator.summary_cards["max_sell_tokens"]),
            max_sell_month=int(simulator.summary_cards["max_sell_month"]),
            circ_12_pct=float(simulator.summary_cards["circ_12_pct"]) if simulator.summary_cards.get("circ_12_pct") is not None else None,
            circ_24_pct=float(simulator.summary_cards["circ_24_pct"]) if simulator.summary_cards.get("circ_24_pct") is not None else None,
            circ_end_pct=float(simulator.summary_cards["circ_end_pct"]) if simulator.summary_cards.get("circ_end_pct") is not None else None
        )

        return SimulationData(
            bucket_results=bucket_results,
            global_metrics=global_metrics,
            summary_cards=summary_cards
        ), simulator.warnings

    @staticmethod
    def validate_config_dict(config_dict: dict) -> Tuple[bool, List[str], List[str]]:
        """
        Validate raw configuration dictionary.

        Args:
            config_dict: Raw configuration dictionary

        Returns:
            Tuple of (is_valid, warnings, errors)
        """
        errors = []
        warnings = []

        try:
            warnings = validate_config(config_dict)
            is_valid = True
        except ValueError as e:
            errors.append(str(e))
            is_valid = False
        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")
            is_valid = False

        return is_valid, warnings, errors
