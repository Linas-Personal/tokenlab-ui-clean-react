"""
Test suite for VestingSimulator

Tests baseline vesting math, behavioral modifiers, edge cases, and data aggregation.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime

from tokenlab_abm.analytics.vesting_simulator import (
    VestingSimulator,
    VestingBucketController,
    validate_config,
    normalize_config,
    DEFAULT_CONFIG,
    SELL_PRESSURE_LEVELS
)


# =============================================================================
# BASELINE VESTING MATH TESTS
# =============================================================================

def test_tge_only_unlock():
    """Test bucket with 100% TGE unlock, no cliff, no vesting."""
    config = {
        "token": {
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "behaviors": {
            "cliff_shock": {"enabled": False},
            "price_trigger": {"enabled": False},
            "relock": {"enabled": False}
        },
        "buckets": [
            {
                "bucket": "Liquidity",
                "allocation": 100,
                "tge_unlock_pct": 100,
                "cliff_months": 0,
                "vesting_months": 0
            }
        ]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    # All tokens should unlock at month 0
    month_0_unlock = df_bucket[df_bucket["month_index"] == 0]["unlocked_this_month"].values[0]
    assert np.isclose(month_0_unlock, 1_000_000, rtol=1e-5)

    # No unlocks after month 0
    later_unlocks = df_bucket[df_bucket["month_index"] > 0]["unlocked_this_month"].sum()
    assert np.isclose(later_unlocks, 0, atol=1e-5)

    # Cumulative at end should equal total supply
    final_unlocked = df_bucket[df_bucket["month_index"] == 12]["unlocked_cumulative"].values[0]
    assert np.isclose(final_unlocked, 1_000_000, rtol=1e-5)


def test_cliff_no_vesting():
    """Test bucket with cliff but no vesting period (all unlocks at cliff end)."""
    config = {
        "token": {
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 24,
            "allocation_mode": "tokens"
        },
        "assumptions": {
            "sell_pressure_level": "low"
        },
        "behaviors": {
            "cliff_shock": {"enabled": False},
            "price_trigger": {"enabled": False},
            "relock": {"enabled": False}
        },
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 1_000_000,
                "tge_unlock_pct": 0,
                "cliff_months": 12,
                "vesting_months": 0
            }
        ]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    # No unlocks during cliff (months 0-12)
    cliff_unlocks = df_bucket[(df_bucket["month_index"] >= 0) &
                               (df_bucket["month_index"] <= 12)]["unlocked_this_month"].sum()
    assert np.isclose(cliff_unlocks, 0, atol=1e-5)

    # All unlocks at month 13 (cliff + 1)
    month_13_unlock = df_bucket[df_bucket["month_index"] == 13]["unlocked_this_month"].values[0]
    assert np.isclose(month_13_unlock, 1_000_000, rtol=1e-5)


def test_standard_cliff_plus_vesting():
    """Test standard cliff + linear vesting schedule."""
    config = {
        "token": {
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 48,
            "allocation_mode": "percent"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "behaviors": {
            "cliff_shock": {"enabled": False},
            "price_trigger": {"enabled": False},
            "relock": {"enabled": False}
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 12,
                "vesting_months": 36
            }
        ]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    # No unlocks during cliff
    cliff_unlocks = df_bucket[(df_bucket["month_index"] >= 0) &
                               (df_bucket["month_index"] <= 12)]["unlocked_this_month"].sum()
    assert np.isclose(cliff_unlocks, 0, atol=1e-5)

    # Linear vesting months 13-48 (36 months)
    expected_monthly_chunk = 1_000_000 / 36
    for month in range(13, 49):
        if month <= 48:
            unlock = df_bucket[df_bucket["month_index"] == month]["unlocked_this_month"].values[0]
            assert np.isclose(unlock, expected_monthly_chunk, rtol=1e-5), f"Month {month} unlock mismatch"

    # Total unlocked at end should equal allocation
    final_unlocked = df_bucket[df_bucket["month_index"] == 48]["unlocked_cumulative"].values[0]
    assert np.isclose(final_unlocked, 1_000_000, rtol=1e-3)


def test_tge_plus_cliff_plus_vesting():
    """Test TGE unlock + cliff + linear vesting."""
    config = {
        "token": {
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 36,
            "allocation_mode": "percent"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "behaviors": {
            "cliff_shock": {"enabled": False},
            "price_trigger": {"enabled": False},
            "relock": {"enabled": False}
        },
        "buckets": [
            {
                "bucket": "Seed",
                "allocation": 100,
                "tge_unlock_pct": 10,
                "cliff_months": 6,
                "vesting_months": 18
            }
        ]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    # TGE unlock
    tge_unlock = df_bucket[df_bucket["month_index"] == 0]["unlocked_this_month"].values[0]
    assert np.isclose(tge_unlock, 100_000, rtol=1e-5)  # 10% of 1M

    # No unlocks during cliff (months 1-6)
    cliff_unlocks = df_bucket[(df_bucket["month_index"] >= 1) &
                               (df_bucket["month_index"] <= 6)]["unlocked_this_month"].sum()
    assert np.isclose(cliff_unlocks, 0, atol=1e-5)

    # Linear vesting months 7-24 (18 months of 900k remaining)
    expected_monthly_chunk = 900_000 / 18
    for month in range(7, 25):
        unlock = df_bucket[df_bucket["month_index"] == month]["unlocked_this_month"].values[0]
        assert np.isclose(unlock, expected_monthly_chunk, rtol=1e-5)

    # Total at end
    final_unlocked = df_bucket[df_bucket["month_index"] == 24]["unlocked_cumulative"].values[0]
    assert np.isclose(final_unlocked, 1_000_000, rtol=1e-3)


def test_multiple_buckets():
    """Test simulation with multiple buckets."""
    config = {
        "token": {
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 24,
            "allocation_mode": "percent"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "behaviors": {
            "cliff_shock": {"enabled": False},
            "price_trigger": {"enabled": False},
            "relock": {"enabled": False}
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 30,
                "tge_unlock_pct": 0,
                "cliff_months": 12,
                "vesting_months": 12
            },
            {
                "bucket": "Investors",
                "allocation": 20,
                "tge_unlock_pct": 10,
                "cliff_months": 3,
                "vesting_months": 9
            },
            {
                "bucket": "Liquidity",
                "allocation": 50,
                "tge_unlock_pct": 100,
                "cliff_months": 0,
                "vesting_months": 0
            }
        ]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    # Check bucket count
    buckets = df_bucket["bucket"].unique()
    assert len(buckets) == 3

    # TGE: Liquidity (50%) + Investors (2%) = 52%
    tge_unlock = df_global[df_global["month_index"] == 0]["total_unlocked"].values[0]
    expected_tge = 500_000 + 20_000  # 50% + 2% (10% of 20%)
    assert np.isclose(tge_unlock, expected_tge, rtol=1e-3)

    # Final cumulative should equal allocations
    final_df = df_bucket[df_bucket["month_index"] == 24]
    total_final = final_df["unlocked_cumulative"].sum()
    assert np.isclose(total_final, 1_000_000, rtol=1e-3)


# =============================================================================
# SELL PRESSURE TESTS
# =============================================================================

def test_sell_pressure_levels():
    """Test different sell pressure levels."""
    for level, expected_pct in SELL_PRESSURE_LEVELS.items():
        config = {
            "token": {
                "total_supply": 1_000_000,
                "start_date": "2026-01-01",
                "horizon_months": 12,
                "allocation_mode": "percent"
            },
            "assumptions": {
                "sell_pressure_level": level
            },
            "behaviors": {
                "cliff_shock": {"enabled": False},
                "price_trigger": {"enabled": False},
                "relock": {"enabled": False}
            },
            "buckets": [
                {
                    "bucket": "Test",
                    "allocation": 100,
                    "tge_unlock_pct": 100,
                    "cliff_months": 0,
                    "vesting_months": 0
                }
            ]
        }

        simulator = VestingSimulator(config)
        df_bucket, df_global = simulator.run_simulation()

        # TGE sell should be unlock * sell_pressure
        tge_unlock = df_bucket[df_bucket["month_index"] == 0]["unlocked_this_month"].values[0]
        expected_sell = tge_unlock * expected_pct
        actual_sell = df_bucket[df_bucket["month_index"] == 0]["expected_sell_this_month"].values[0]

        assert np.isclose(actual_sell, expected_sell, rtol=1e-5), f"Sell pressure {level} mismatch"


def test_cliff_shock():
    """Test cliff shock multiplier on first vest month."""
    config = {
        "token": {
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 24,
            "allocation_mode": "percent"
        },
        "assumptions": {
            "sell_pressure_level": "medium"  # 0.25 base
        },
        "behaviors": {
            "cliff_shock": {
                "enabled": True,
                "multiplier": 3.0,
                "buckets": ["Team"]
            },
            "price_trigger": {"enabled": False},
            "relock": {"enabled": False}
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 12,
                "vesting_months": 12
            }
        ]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    # Month 13: first vest month should have 3x sell pressure
    month_13_unlock = df_bucket[df_bucket["month_index"] == 13]["unlocked_this_month"].values[0]
    month_13_sell = df_bucket[df_bucket["month_index"] == 13]["expected_sell_this_month"].values[0]

    expected_sell_with_shock = month_13_unlock * 0.25 * 3.0  # base * multiplier
    assert np.isclose(month_13_sell, expected_sell_with_shock, rtol=1e-5)

    # Month 14: back to normal sell pressure
    month_14_unlock = df_bucket[df_bucket["month_index"] == 14]["unlocked_this_month"].values[0]
    month_14_sell = df_bucket[df_bucket["month_index"] == 14]["expected_sell_this_month"].values[0]

    expected_sell_normal = month_14_unlock * 0.25
    assert np.isclose(month_14_sell, expected_sell_normal, rtol=1e-5)


def test_cliff_shock_only_if_cliff_gt_zero():
    """Test that cliff shock doesn't apply if cliff = 0."""
    config = {
        "token": {
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "behaviors": {
            "cliff_shock": {
                "enabled": True,
                "multiplier": 3.0,
                "buckets": ["Test"]
            },
            "price_trigger": {"enabled": False},
            "relock": {"enabled": False}
        },
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 0,  # No cliff
                "vesting_months": 12
            }
        ]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    # Month 1: first vest month, but cliff = 0, so NO shock
    month_1_unlock = df_bucket[df_bucket["month_index"] == 1]["unlocked_this_month"].values[0]
    month_1_sell = df_bucket[df_bucket["month_index"] == 1]["expected_sell_this_month"].values[0]

    expected_sell_no_shock = month_1_unlock * 0.25  # Normal sell pressure
    assert np.isclose(month_1_sell, expected_sell_no_shock, rtol=1e-5)


def test_price_trigger_take_profit():
    """Test price trigger with uptrend scenario (take-profit)."""
    config = {
        "token": {
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 24,
            "allocation_mode": "percent"
        },
        "assumptions": {
            "sell_pressure_level": "low"  # 0.10 base
        },
        "behaviors": {
            "cliff_shock": {"enabled": False},
            "price_trigger": {
                "enabled": True,
                "source": "scenario",
                "scenario": "uptrend",  # Price increases by 5% per month
                "take_profit": 0.5,  # Trigger at +50%
                "stop_loss": -0.3,
                "extra_sell_addon": 0.2  # Add 20% sell pressure
            },
            "relock": {"enabled": False}
        },
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 24
            }
        ]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    # Month 0: price = 1.0, no trigger
    month_0_sell_pressure = df_bucket[df_bucket["month_index"] == 0]["sell_pressure_effective"].values[0]
    assert np.isclose(month_0_sell_pressure, 0.10, rtol=1e-5)

    # Month 10: price = 1.05^10 ≈ 1.63 (+63%), should trigger
    # Sell pressure should be 0.10 + 0.20 = 0.30
    month_10_sell_pressure = df_bucket[df_bucket["month_index"] == 10]["sell_pressure_effective"].values[0]
    assert np.isclose(month_10_sell_pressure, 0.30, rtol=1e-5)


def test_relock():
    """Test relock mechanism."""
    config = {
        "token": {
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 24,
            "allocation_mode": "percent"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "behaviors": {
            "cliff_shock": {"enabled": False},
            "price_trigger": {"enabled": False},
            "relock": {
                "enabled": True,
                "relock_pct": 0.30,  # 30% relocked
                "lock_duration_months": 6
            }
        },
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 12
            }
        ]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    # Month 1: unlock 1/12 of 1M = 83,333
    # Relock doesn't apply to TGE (month 0), so month 1 is first relock
    month_1_unlock = df_bucket[df_bucket["month_index"] == 1]["unlocked_this_month"].values[0]
    expected_unlock = 1_000_000 / 12
    assert np.isclose(month_1_unlock, expected_unlock, rtol=1e-3)

    # Only 70% is free to sell immediately
    # 30% is relocked and matures at month 7 (1 + 6)
    month_1_sell = df_bucket[df_bucket["month_index"] == 1]["expected_sell_this_month"].values[0]
    expected_sell_month_1 = expected_unlock * 0.70 * 0.25  # 70% free * medium sell pressure
    assert np.isclose(month_1_sell, expected_sell_month_1, rtol=1e-3)

    # Month 7: should have both new unlock AND matured relock from month 1
    month_7_unlock = df_bucket[df_bucket["month_index"] == 7]["unlocked_this_month"].values[0]
    assert np.isclose(month_7_unlock, expected_unlock, rtol=1e-3)

    # Expected sell should include matured relock
    # Free from month 7 = 83,333 * 0.70 = 58,333
    # Matured from month 1 = 83,333 * 0.30 = 25,000
    # Total available = 58,333 + 25,000 = 83,333
    # Sell = 83,333 * 0.25 = 20,833
    month_7_sell = df_bucket[df_bucket["month_index"] == 7]["expected_sell_this_month"].values[0]
    expected_available = expected_unlock * 0.70 + expected_unlock * 0.30
    expected_sell_month_7 = expected_available * 0.25
    assert np.isclose(month_7_sell, expected_sell_month_7, rtol=1e-3)


# =============================================================================
# VALIDATION TESTS
# =============================================================================

def test_validation_negative_supply():
    """Test validation catches negative supply."""
    config = {
        "token": {
            "total_supply": -1000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent"
        },
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {},
        "buckets": []
    }

    with pytest.raises(ValueError, match="total_supply must be positive"):
        validate_config(config)


def test_validation_invalid_date():
    """Test validation catches invalid date format."""
    config = {
        "token": {
            "total_supply": 1000,
            "start_date": "2026/01/01",  # Wrong format
            "horizon_months": 12,
            "allocation_mode": "percent"
        },
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {},
        "buckets": []
    }

    with pytest.raises(ValueError, match="start_date must be in YYYY-MM-DD format"):
        validate_config(config)


def test_validation_tge_out_of_range():
    """Test validation catches TGE unlock % out of range."""
    config = {
        "token": {
            "total_supply": 1000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent"
        },
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {},
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": 150,  # Invalid
                "cliff_months": 0,
                "vesting_months": 12
            }
        ]
    }

    with pytest.raises(ValueError, match="tge_unlock_pct must be between 0 and 100"):
        validate_config(config)


def test_validation_allocation_exceeds_100_percent():
    """Test validation catches allocation sum > 100% in percent mode."""
    config = {
        "token": {
            "total_supply": 1000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent"
        },
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {},
        "buckets": [
            {
                "bucket": "A",
                "allocation": 60,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 12
            },
            {
                "bucket": "B",
                "allocation": 60,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 12
            }
        ]
    }

    with pytest.raises(ValueError, match="exceeds 100%"):
        validate_config(config)


def test_validation_allocation_warning_under_100():
    """Test validation warns when allocation sum < 100%."""
    config = {
        "token": {
            "total_supply": 1000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent"
        },
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {},
        "buckets": [
            {
                "bucket": "A",
                "allocation": 50,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 12
            }
        ]
    }

    warnings = validate_config(config)
    assert len(warnings) == 1
    assert "50" in warnings[0] and "unallocated" in warnings[0]


# =============================================================================
# DATA AGGREGATION TESTS
# =============================================================================

def test_dataframe_structure():
    """Test that output dataframes have correct structure."""
    config = {
        "token": {
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent"
        },
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {
            "cliff_shock": {"enabled": False},
            "price_trigger": {"enabled": False},
            "relock": {"enabled": False}
        },
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": 100,
                "cliff_months": 0,
                "vesting_months": 0
            }
        ]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    # Check df_bucket columns
    expected_bucket_cols = [
        "month_index", "date", "bucket", "allocation_tokens",
        "unlocked_this_month", "unlocked_cumulative", "locked_remaining",
        "sell_pressure_effective", "expected_sell_this_month",
        "expected_circulating_cumulative"
    ]
    assert all(col in df_bucket.columns for col in expected_bucket_cols)

    # Check df_global columns
    expected_global_cols = [
        "month_index", "date", "total_unlocked", "total_expected_sell",
        "expected_circulating_total", "expected_circulating_pct",
        "sell_volume_ratio"
    ]
    assert all(col in df_global.columns for col in expected_global_cols)

    # Check row counts (13 months: 0-12)
    assert len(df_bucket) == 13
    assert len(df_global) == 13


def test_summary_cards():
    """Test summary card calculations."""
    config = {
        "token": {
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 36,
            "allocation_mode": "percent"
        },
        "assumptions": {"sell_pressure_level": "high"},
        "behaviors": {
            "cliff_shock": {"enabled": False},
            "price_trigger": {"enabled": False},
            "relock": {"enabled": False}
        },
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 12,
                "vesting_months": 24
            }
        ]
    }

    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    # Max unlock should be at month 13 (first vest month)
    assert simulator.summary_cards["max_unlock_month"] == 13

    # Max sell should be at month 13 (highest sell pressure)
    assert simulator.summary_cards["max_sell_month"] == 13

    # Circulating should be 0 at month 12, some % at month 24, and higher at end
    assert simulator.summary_cards["circ_12_pct"] is not None
    assert simulator.summary_cards["circ_24_pct"] is not None
    assert simulator.summary_cards["circ_end_pct"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
