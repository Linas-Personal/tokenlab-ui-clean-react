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
    validate_config,
    normalize_config
)

from app.models.request import SimulationConfig
from app.models.response import (
    BucketResult,
    GlobalMetric,
    SummaryCards,
    SimulationData
)


class SimulatorService:
    """Service class for running vesting simulations."""

    @staticmethod
    def _convert_config_to_dict(config: SimulationConfig) -> dict:
        """
        Convert Pydantic model to dict format expected by VestingSimulator.

        Args:
            config: Pydantic SimulationConfig model

        Returns:
            Dictionary in VestingSimulator format
        """
        config_dict = {
            "token": {
                "name": config.token.name,
                "total_supply": config.token.total_supply,
                "start_date": config.token.start_date,
                "horizon_months": config.token.horizon_months,
                "allocation_mode": config.token.allocation_mode,
                "simulation_mode": config.token.simulation_mode
            },
            "assumptions": {
                "sell_pressure_level": config.assumptions.sell_pressure_level,
                "avg_daily_volume_tokens": config.assumptions.avg_daily_volume_tokens
            },
            "behaviors": {
                "cliff_shock": {
                    "enabled": config.behaviors.cliff_shock.enabled,
                    "multiplier": config.behaviors.cliff_shock.multiplier,
                    "buckets": config.behaviors.cliff_shock.buckets
                },
                "price_trigger": {
                    "enabled": config.behaviors.price_trigger.enabled,
                    "source": config.behaviors.price_trigger.source,
                    "scenario": config.behaviors.price_trigger.scenario,
                    "take_profit": config.behaviors.price_trigger.take_profit,
                    "stop_loss": config.behaviors.price_trigger.stop_loss,
                    "extra_sell_addon": config.behaviors.price_trigger.extra_sell_addon,
                    "uploaded_price_series": config.behaviors.price_trigger.uploaded_price_series
                },
                "relock": {
                    "enabled": config.behaviors.relock.enabled,
                    "relock_pct": config.behaviors.relock.relock_pct,
                    "lock_duration_months": config.behaviors.relock.lock_duration_months
                }
            },
            "buckets": [
                {
                    "bucket": b.bucket,
                    "allocation": b.allocation,
                    "tge_unlock_pct": b.tge_unlock_pct,
                    "cliff_months": b.cliff_months,
                    "vesting_months": b.vesting_months,
                    "unlock_type": b.unlock_type
                }
                for b in config.buckets
            ]
        }

        # Add Tier 2 config if present
        if config.tier2 is not None:
            config_dict["tier2"] = {
                "staking": {
                    "enabled": config.tier2.staking.enabled,
                    "apy": config.tier2.staking.apy,
                    "max_capacity_pct": config.tier2.staking.max_capacity_pct,
                    "lockup_months": config.tier2.staking.lockup_months,
                    "participation_rate": config.tier2.staking.participation_rate,
                    "reward_source": config.tier2.staking.reward_source
                },
                "pricing": {
                    "enabled": config.tier2.pricing.enabled,
                    "pricing_model": config.tier2.pricing.pricing_model,
                    "initial_price": config.tier2.pricing.initial_price,
                    "target_price": config.tier2.pricing.target_price,
                    "bonding_curve_param": config.tier2.pricing.bonding_curve_param
                },
                "treasury": {
                    "enabled": config.tier2.treasury.enabled,
                    "initial_balance_pct": config.tier2.treasury.initial_balance_pct,
                    "hold_pct": config.tier2.treasury.hold_pct,
                    "liquidity_pct": config.tier2.treasury.liquidity_pct,
                    "buyback_pct": config.tier2.treasury.buyback_pct
                },
                "volume": {
                    "enabled": config.tier2.volume.enabled,
                    "volume_model": config.tier2.volume.volume_model,
                    "base_daily_volume": config.tier2.volume.base_daily_volume,
                    "volume_multiplier": config.tier2.volume.volume_multiplier
                }
            }

        # Add Tier 3 config if present
        if config.tier3 is not None:
            config_dict["tier3"] = {
                "cohort_behavior": {
                    "enabled": config.tier3.cohort_behavior.enabled,
                    "profiles": {
                        name: {
                            "sell_pressure_mean": profile.sell_pressure_mean,
                            "sell_pressure_std": profile.sell_pressure_std,
                            "stake_probability": profile.stake_probability,
                            "hold_probability": profile.hold_probability
                        }
                        for name, profile in config.tier3.cohort_behavior.profiles.items()
                    },
                    "bucket_cohort_mapping": config.tier3.cohort_behavior.bucket_cohort_mapping
                },
                "monte_carlo": {
                    "enabled": config.tier3.monte_carlo.enabled,
                    "num_trials": config.tier3.monte_carlo.num_trials,
                    "variance_level": config.tier3.monte_carlo.variance_level,
                    "seed": config.tier3.monte_carlo.seed
                }
            }

        return config_dict

    @staticmethod
    def _serialize_dataframe_to_bucket_results(df: pd.DataFrame) -> List[BucketResult]:
        """
        Convert bucket DataFrame to list of BucketResult models.

        Args:
            df: Bucket results DataFrame

        Returns:
            List of BucketResult models
        """
        records = df.to_dict(orient="records")

        return [
            BucketResult(
                month_index=int(r["month_index"]),
                date=r["date"],
                bucket=r["bucket"],
                allocation_tokens=float(r["allocation_tokens"]),
                unlocked_this_month=float(r["unlocked_this_month"]),
                unlocked_cumulative=float(r["unlocked_cumulative"]),
                locked_remaining=float(r["locked_remaining"]),
                sell_pressure_effective=float(r["sell_pressure_effective"]),
                expected_sell_this_month=float(r["expected_sell_this_month"]),
                expected_circulating_cumulative=float(r["expected_circulating_cumulative"])
            )
            for r in records
        ]

    @staticmethod
    def _serialize_dataframe_to_global_metrics(df: pd.DataFrame) -> List[GlobalMetric]:
        """
        Convert global DataFrame to list of GlobalMetric models.

        Args:
            df: Global metrics DataFrame

        Returns:
            List of GlobalMetric models
        """
        records = df.to_dict(orient="records")

        return [
            GlobalMetric(
                month_index=int(r["month_index"]),
                date=r["date"],
                total_unlocked=float(r["total_unlocked"]),
                total_expected_sell=float(r["total_expected_sell"]),
                expected_circulating_total=float(r["expected_circulating_total"]),
                expected_circulating_pct=float(r["expected_circulating_pct"]),
                sell_volume_ratio=float(r["sell_volume_ratio"]) if r.get("sell_volume_ratio") is not None else None,
                current_price=float(r["current_price"]) if r.get("current_price") is not None else None,
                staked_amount=float(r["staked_amount"]) if r.get("staked_amount") is not None else None,
                liquidity_deployed=float(r["liquidity_deployed"]) if r.get("liquidity_deployed") is not None else None,
                treasury_balance=float(r["treasury_balance"]) if r.get("treasury_balance") is not None else None
            )
            for r in records
        ]

    @staticmethod
    def _convert_summary_cards(summary: dict) -> SummaryCards:
        """
        Convert summary cards dict to Pydantic model.

        Args:
            summary: Summary cards dictionary

        Returns:
            SummaryCards model
        """
        return SummaryCards(
            max_unlock_tokens=float(summary["max_unlock_tokens"]),
            max_unlock_month=int(summary["max_unlock_month"]),
            max_sell_tokens=float(summary["max_sell_tokens"]),
            max_sell_month=int(summary["max_sell_month"]),
            circ_12_pct=float(summary["circ_12_pct"]),
            circ_24_pct=float(summary["circ_24_pct"]),
            circ_end_pct=float(summary["circ_end_pct"])
        )

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
        # Convert Pydantic model to dict
        config_dict = cls._convert_config_to_dict(config)

        # Select appropriate simulator class based on mode
        mode = config.token.simulation_mode

        if mode == "tier1":
            simulator = VestingSimulator(config_dict, mode="tier1")
        elif mode in ["tier2", "tier3"]:
            simulator = VestingSimulatorAdvanced(config_dict, mode=mode)
        else:
            raise ValueError(f"Invalid simulation mode: {mode}")

        # Run simulation
        df_bucket, df_global = simulator.run_simulation()

        # Convert results to Pydantic models
        bucket_results = cls._serialize_dataframe_to_bucket_results(df_bucket)
        global_metrics = cls._serialize_dataframe_to_global_metrics(df_global)
        summary_cards = cls._convert_summary_cards(simulator.summary_cards)

        simulation_data = SimulationData(
            bucket_results=bucket_results,
            global_metrics=global_metrics,
            summary_cards=summary_cards
        )

        return simulation_data, simulator.warnings

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
            # Use existing validation from vesting_simulator
            warnings = validate_config(config_dict)
            is_valid = True
        except ValueError as e:
            errors.append(str(e))
            is_valid = False
        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")
            is_valid = False

        return is_valid, warnings, errors
