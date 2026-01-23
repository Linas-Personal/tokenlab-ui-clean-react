"""
Comprehensive edge case and integration testing for vesting simulator.

Tests boundary conditions, error handling, invalid inputs, and real integration scenarios.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime

# Set matplotlib to non-GUI backend for testing
import matplotlib
matplotlib.use('Agg')

from tokenlab_abm.analytics.vesting_simulator import (
    VestingSimulator,
    VestingSimulatorAdvanced,
    VestingBucketController,
    VestingTokenEconomy,
    DynamicStakingController,
    DynamicPricingController,
    TreasuryStrategyController,
    MonteCarloRunner,
    CohortBehaviorController,
    validate_config,
    normalize_config
)


# =============================================================================
# BOUNDARY CONDITIONS & EDGE CASES
# =============================================================================

def test_zero_supply():
    """Test handling of zero total supply."""
    config = {
        "token": {"total_supply": 0, "start_date": "2026-01-01", "horizon_months": 12, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {"cliff_shock": {"enabled": False}, "price_trigger": {"enabled": False}, "relock": {"enabled": False}},
        "buckets": [{"bucket": "Test", "allocation": 100, "tge_unlock_pct": 0, "cliff_months": 6, "vesting_months": 6}]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    assert len(df_global) > 0
    assert df_global["total_unlocked"].sum() == 0


def test_zero_horizon():
    """Test zero month horizon (TGE only)."""
    config = {
        "token": {"total_supply": 1_000_000, "start_date": "2026-01-01", "horizon_months": 0, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {"cliff_shock": {"enabled": False}, "price_trigger": {"enabled": False}, "relock": {"enabled": False}},
        "buckets": [{"bucket": "Test", "allocation": 100, "tge_unlock_pct": 100, "cliff_months": 0, "vesting_months": 0}]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    assert len(df_global) == 1  # Only month 0
    assert df_global.iloc[0]["total_unlocked"] == pytest.approx(1_000_000, rel=1e-5)


def test_empty_buckets_list():
    """Test with no allocation buckets."""
    config = {
        "token": {"total_supply": 1_000_000, "start_date": "2026-01-01", "horizon_months": 12, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {"cliff_shock": {"enabled": False}, "price_trigger": {"enabled": False}, "relock": {"enabled": False}},
        "buckets": []
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    assert len(df_global) > 0
    assert df_global["total_unlocked"].sum() == 0


def test_100_percent_cliff_shock():
    """Test cliff shock with 100% sell pressure."""
    config = {
        "token": {"total_supply": 1_000_000, "start_date": "2026-01-01", "horizon_months": 24, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "low"},  # 10% base
        "behaviors": {
            "cliff_shock": {"enabled": True, "multiplier": 10.0, "buckets": ["Test"]},  # Would be 100%+
            "price_trigger": {"enabled": False},
            "relock": {"enabled": False}
        },
        "buckets": [{"bucket": "Test", "allocation": 100, "tge_unlock_pct": 0, "cliff_months": 12, "vesting_months": 12}]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    # Cliff shock should be capped at 100%
    month_13_sell = df_global[df_global["month_index"] == 13]["total_expected_sell"].values[0]
    month_13_unlock = df_global[df_global["month_index"] == 13]["total_unlocked"].values[0]

    assert month_13_sell <= month_13_unlock  # Can't sell more than unlocked


def test_tier2_all_features_disabled():
    """Test Tier 2 with all dynamic features disabled."""
    config = {
        "token": {"total_supply": 1_000_000, "start_date": "2026-01-01", "horizon_months": 12, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {"cliff_shock": {"enabled": False}, "price_trigger": {"enabled": False}, "relock": {"enabled": False}},
        "tier2": {
            "staking": {"enabled": False},
            "pricing": {"enabled": False},
            "treasury": {"enabled": False},
            "volume": {"enabled": False}
        },
        "buckets": [{"bucket": "Test", "allocation": 100, "tge_unlock_pct": 0, "cliff_months": 6, "vesting_months": 6}]
    }

    simulator = VestingSimulatorAdvanced(config, mode="tier2")
    df_bucket, df_global = simulator.run_simulation()
    figs = simulator.make_charts(df_bucket, df_global)

    assert len(df_global) > 0
    assert len(figs) == 3  # Only base charts, no Tier 2 charts


def test_tier2_extreme_apy():
    """Test staking with extreme APY values."""
    config = {
        "token": {"total_supply": 1_000_000, "start_date": "2026-01-01", "horizon_months": 12, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {"cliff_shock": {"enabled": False}, "price_trigger": {"enabled": False}, "relock": {"enabled": False}},
        "tier2": {
            "staking": {"enabled": True, "apy": 5.0, "capacity": 0.99, "lockup": 1, "include_rewards": True},  # 500% APY
            "pricing": {"enabled": False},
            "treasury": {"enabled": False},
            "volume": {"enabled": False}
        },
        "buckets": [{"bucket": "Test", "allocation": 100, "tge_unlock_pct": 0, "cliff_months": 1, "vesting_months": 6}]
    }

    simulator = VestingSimulatorAdvanced(config, mode="tier2")
    df_bucket, df_global = simulator.run_simulation()

    # Supply should increase due to rewards
    initial_supply = config["token"]["total_supply"]
    final_supply = simulator.vesting_economy.supply
    assert final_supply > initial_supply  # Rewards added


def test_tier2_bonding_curve_extreme_elasticity():
    """Test bonding curve with extreme elasticity."""
    config = {
        "token": {"total_supply": 1_000_000, "start_date": "2026-01-01", "horizon_months": 12, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "low"},
        "behaviors": {"cliff_shock": {"enabled": False}, "price_trigger": {"enabled": False}, "relock": {"enabled": False}},
        "tier2": {
            "staking": {"enabled": False},
            "pricing": {"enabled": True, "model": "bonding_curve", "initial_price": 1.0, "elasticity": 0.99},
            "treasury": {"enabled": False},
            "volume": {"enabled": False}
        },
        "buckets": [{"bucket": "Test", "allocation": 100, "tge_unlock_pct": 10, "cliff_months": 0, "vesting_months": 12}]
    }

    simulator = VestingSimulatorAdvanced(config, mode="tier2")
    df_bucket, df_global = simulator.run_simulation()

    # Price should decrease significantly as supply increases
    prices = df_global["current_price"].values
    assert prices[0] > prices[-1]  # Price drops over time
    assert all(p > 0 for p in prices)  # Never negative


def test_tier3_monte_carlo_single_trial():
    """Test Monte Carlo with just 1 trial (edge case)."""
    config = {
        "token": {"total_supply": 1_000_000, "start_date": "2026-01-01", "horizon_months": 6, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {"cliff_shock": {"enabled": False}, "price_trigger": {"enabled": False}, "relock": {"enabled": False}},
        "tier2": {"staking": {"enabled": False}, "pricing": {"enabled": False}, "treasury": {"enabled": False}, "volume": {"enabled": False}},
        "buckets": [{"bucket": "Test", "allocation": 100, "tge_unlock_pct": 0, "cliff_months": 3, "vesting_months": 3}]
    }

    runner = MonteCarloRunner(config, variance_level=0.10)
    df_stats, df_combined = runner.run(num_trials=1, mode="tier1")

    assert len(df_stats) == 7  # 7 months (0-6)
    assert df_combined["trial"].nunique() == 1


def test_treasury_unbalanced_percentages():
    """Test treasury with percentages that don't sum to 1.0."""
    config = {
        "token": {"total_supply": 1_000_000, "start_date": "2026-01-01", "horizon_months": 12, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {"cliff_shock": {"enabled": False}, "price_trigger": {"enabled": False}, "relock": {"enabled": False}},
        "tier2": {
            "staking": {"enabled": False},
            "pricing": {"enabled": False},
            "treasury": {"enabled": True, "hold_pct": 0.5, "liquidity_pct": 0.3, "buyback_pct": 0.5},  # Sums to 1.3
            "volume": {"enabled": False}
        },
        "buckets": [
            {"bucket": "Treasury", "allocation": 100, "tge_unlock_pct": 0, "cliff_months": 0, "vesting_months": 12}
        ]
    }

    simulator = VestingSimulatorAdvanced(config, mode="tier2")
    df_bucket, df_global = simulator.run_simulation()

    # Should normalize automatically
    assert len(df_global) > 0


# =============================================================================
# ERROR HANDLING & INVALID INPUTS
# =============================================================================

def test_invalid_date_format():
    """Test with invalid date format."""
    config = {
        "token": {"total_supply": 1_000_000, "start_date": "01/01/2026", "horizon_months": 12, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {"cliff_shock": {"enabled": False}, "price_trigger": {"enabled": False}, "relock": {"enabled": False}},
        "buckets": [{"bucket": "Test", "allocation": 100, "tge_unlock_pct": 0, "cliff_months": 6, "vesting_months": 6}]
    }

    warnings = validate_config(config)
    assert any("YYYY-MM-DD" in w for w in warnings)


def test_negative_cliff_months():
    """Test with negative cliff months."""
    config = {
        "token": {"total_supply": 1_000_000, "start_date": "2026-01-01", "horizon_months": 12, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {"cliff_shock": {"enabled": False}, "price_trigger": {"enabled": False}, "relock": {"enabled": False}},
        "buckets": [{"bucket": "Test", "allocation": 100, "tge_unlock_pct": 0, "cliff_months": -5, "vesting_months": 6}]
    }

    # Should normalize negative to 0
    normalized = normalize_config(config)
    assert normalized["buckets"][0]["cliff_months"] >= 0


def test_tge_unlock_over_100():
    """Test with TGE unlock > 100% - should be clamped to 100."""
    config = {
        "token": {"total_supply": 1_000_000, "start_date": "2026-01-01", "horizon_months": 12, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {"cliff_shock": {"enabled": False}, "price_trigger": {"enabled": False}, "relock": {"enabled": False}},
        "buckets": [{"bucket": "Test", "allocation": 100, "tge_unlock_pct": 150, "cliff_months": 0, "vesting_months": 0}]
    }

    # Normalize should clamp to 100
    normalized = normalize_config(config)
    assert normalized["buckets"][0]["tge_unlock_pct"] == 100


def test_missing_required_config_keys():
    """Test with missing required configuration keys."""
    config = {
        "token": {"total_supply": 1_000_000},  # Missing start_date, horizon_months
        "assumptions": {"sell_pressure_level": "medium"},
        "buckets": []
    }

    # normalize_config should add defaults
    normalized = normalize_config(config)
    assert "start_date" in normalized["token"]
    assert "horizon_months" in normalized["token"]


def test_none_values_in_config():
    """Test with None values in configuration."""
    config = {
        "token": {"total_supply": 1_000_000, "start_date": "2026-01-01", "horizon_months": 12, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "medium", "avg_daily_volume_tokens": None},
        "behaviors": {"cliff_shock": {"enabled": False}, "price_trigger": {"enabled": False}, "relock": {"enabled": False}},
        "buckets": [{"bucket": "Test", "allocation": 100, "tge_unlock_pct": 0, "cliff_months": 6, "vesting_months": 6}]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    assert len(df_global) > 0
    # sell_volume_ratio should handle None volume gracefully


# =============================================================================
# INTEGRATION TESTS WITH REAL DEPENDENCIES
# =============================================================================

def test_full_tier1_simulation_with_all_modifiers():
    """Integration test with all Tier 1 modifiers enabled."""
    config = {
        "token": {"total_supply": 1_000_000_000, "start_date": "2026-01-01", "horizon_months": 36, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "medium", "avg_daily_volume_tokens": 5_000_000},
        "behaviors": {
            "cliff_shock": {"enabled": True, "multiplier": 3.0, "buckets": ["Seed", "Private"]},
            "price_trigger": {"enabled": True, "source": "scenario", "scenario": "volatile", "take_profit": 0.5, "stop_loss": -0.3, "extra_sell_addon": 0.2, "uploaded_price_series": None},
            "relock": {"enabled": True, "relock_pct": 0.4, "lock_duration_months": 6}
        },
        "buckets": [
            {"bucket": "Team", "allocation": 20, "tge_unlock_pct": 0, "cliff_months": 12, "vesting_months": 36},
            {"bucket": "Seed", "allocation": 10, "tge_unlock_pct": 10, "cliff_months": 6, "vesting_months": 18},
            {"bucket": "Private", "allocation": 15, "tge_unlock_pct": 15, "cliff_months": 3, "vesting_months": 12},
            {"bucket": "Treasury", "allocation": 30, "tge_unlock_pct": 0, "cliff_months": 0, "vesting_months": 48},
            {"bucket": "Liquidity", "allocation": 25, "tge_unlock_pct": 100, "cliff_months": 0, "vesting_months": 0}
        ]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()
    figs = simulator.make_charts(df_bucket, df_global)

    # Verify all outputs
    assert len(df_bucket) > 0
    assert len(df_global) == 37  # 37 months (0-36)
    assert len(figs) == 3
    assert simulator.summary_cards is not None
    assert "max_unlock_tokens" in simulator.summary_cards

    # Verify relock is working
    assert len(simulator.bucket_controllers) == 5
    team_controller = [c for c in simulator.bucket_controllers if c.config["bucket"] == "Team"][0]
    assert len(team_controller.relock_schedule) > 0  # Some tokens relocked

    # Export tests
    import tempfile
    temp_dir = tempfile.mkdtemp()
    csv1, csv2 = simulator.export_csvs(temp_dir)
    assert csv1.endswith(".csv")
    assert csv2.endswith(".csv")

    pdf_path = simulator.export_pdf(f"{temp_dir}/report.pdf")
    assert pdf_path.endswith(".pdf")

    json_str = simulator.to_json()
    assert len(json_str) > 0


def test_full_tier2_simulation_all_features():
    """Integration test with all Tier 2 features enabled."""
    config = {
        "token": {"total_supply": 1_000_000_000, "start_date": "2026-01-01", "horizon_months": 24, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {"cliff_shock": {"enabled": False}, "price_trigger": {"enabled": False}, "relock": {"enabled": False}},
        "tier2": {
            "staking": {"enabled": True, "apy": 0.20, "capacity": 0.70, "lockup": 6, "include_rewards": True},
            "pricing": {"enabled": True, "model": "bonding_curve", "initial_price": 2.0, "elasticity": 0.6},
            "treasury": {"enabled": True, "hold_pct": 0.3, "liquidity_pct": 0.5, "buyback_pct": 0.2},
            "volume": {"enabled": True, "turnover_rate": 0.02}
        },
        "buckets": [
            {"bucket": "Team", "allocation": 25, "tge_unlock_pct": 0, "cliff_months": 12, "vesting_months": 24},
            {"bucket": "Investors", "allocation": 20, "tge_unlock_pct": 10, "cliff_months": 6, "vesting_months": 18},
            {"bucket": "Treasury", "allocation": 35, "tge_unlock_pct": 0, "cliff_months": 0, "vesting_months": 36},
            {"bucket": "Liquidity", "allocation": 20, "tge_unlock_pct": 100, "cliff_months": 0, "vesting_months": 0}
        ]
    }

    simulator = VestingSimulatorAdvanced(config, mode="tier2")
    df_bucket, df_global = simulator.run_simulation()
    figs = simulator.make_charts(df_bucket, df_global)

    # Verify Tier 2 components are active
    assert simulator.staking_controller is not None
    assert simulator.pricing_controller is not None
    assert simulator.treasury_controller is not None
    assert simulator.volume_calculator is not None

    # Verify price evolution
    assert "current_price" in df_global.columns
    prices = df_global["current_price"].values
    assert all(p > 0 for p in prices)

    # Verify staking occurred
    assert sum(simulator.staking_controller._staked_this_month) > 0

    # Verify charts include Tier 2 charts
    assert len(figs) >= 3  # At least base charts


def test_full_tier3_with_cohorts_and_monte_carlo():
    """Integration test with Tier 3 cohorts and Monte Carlo."""
    config = {
        "token": {"total_supply": 1_000_000, "start_date": "2026-01-01", "horizon_months": 12, "allocation_mode": "percent"},
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {"cliff_shock": {"enabled": False}, "price_trigger": {"enabled": False}, "relock": {"enabled": False}},
        "tier2": {
            "staking": {"enabled": True, "apy": 0.15, "capacity": 0.60, "lockup": 6, "include_rewards": True},
            "pricing": {"enabled": False},
            "treasury": {"enabled": False},
            "volume": {"enabled": False}
        },
        "tier3": {
            "cohorts": {
                "enabled": True,
                "bucket_profiles": {
                    "Team": "high_stake",
                    "VCs": "high_sell",
                    "Community": "balanced"
                }
            }
        },
        "buckets": [
            {"bucket": "Team", "allocation": 40, "tge_unlock_pct": 0, "cliff_months": 12, "vesting_months": 12},
            {"bucket": "VCs", "allocation": 30, "tge_unlock_pct": 10, "cliff_months": 6, "vesting_months": 12},
            {"bucket": "Community", "allocation": 30, "tge_unlock_pct": 20, "cliff_months": 3, "vesting_months": 12}
        ]
    }

    # Test cohort simulation
    simulator = VestingSimulatorAdvanced(config, mode="tier3")
    df_bucket, df_global = simulator.run_simulation()

    assert simulator.cohort_controller is not None

    # Verify different cohorts have different behavior
    team_mult = simulator.cohort_controller.get_behavior_multiplier("Team")
    vc_mult = simulator.cohort_controller.get_behavior_multiplier("VCs")
    assert vc_mult > team_mult  # VCs sell more

    # Test Monte Carlo
    runner = MonteCarloRunner(config, variance_level=0.10)
    df_stats, df_combined = runner.run(num_trials=50, mode="tier3")

    assert len(df_stats) > 0
    assert df_combined["trial"].nunique() == 50
    assert "total_unlocked_median" in df_stats.columns
    assert "total_expected_sell_median" in df_stats.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
