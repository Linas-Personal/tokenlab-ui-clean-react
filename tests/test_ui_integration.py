"""
Integration test for UI workflow with invalid inputs.

This test verifies the complete UI flow:
1. Create config with invalid values
2. Validate (get warnings)
3. Normalize (fix invalid values)
4. Run simulation
5. Generate charts

This ensures the normalize_config fix actually prevents the NoneType error.
"""

import pytest
from tokenlab_abm.analytics.vesting_simulator import (
    VestingSimulator,
    VestingSimulatorAdvanced,
    validate_config,
    normalize_config
)


def test_ui_workflow_with_invalid_inputs_tier1():
    """Test complete UI workflow with invalid inputs for Tier 1."""
    # Create config with invalid values (as might come from UI)
    config = {
        "token": {
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 24,
            "allocation_mode": "percent",
            "simulation_mode": "tier1"
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
                "allocation": 50,
                "tge_unlock_pct": 150,  # INVALID: > 100%
                "cliff_months": -6,  # INVALID: negative
                "vesting_months": 12
            },
            {
                "bucket": "Investors",
                "allocation": 50,
                "tge_unlock_pct": 10,
                "cliff_months": 6,
                "vesting_months": 12
            }
        ]
    }

    # Step 1: Validate (should return warnings, not crash)
    warnings = validate_config(config)
    assert len(warnings) > 0
    assert any("tge_unlock_pct" in w for w in warnings)
    assert any("cliff_months" in w for w in warnings)

    # Step 2: Normalize (should fix invalid values)
    config = normalize_config(config)

    # Verify normalization fixed the issues
    assert config["buckets"][0]["tge_unlock_pct"] == 100  # Clamped to 100
    assert config["buckets"][0]["cliff_months"] == 0  # Clamped to 0

    # Step 3: Run simulation (should not crash)
    simulator = VestingSimulator(config, mode="tier1")
    df_bucket, df_global = simulator.run_simulation()

    # Verify simulation ran successfully
    assert len(df_bucket) > 0
    assert len(df_global) > 0

    # Step 4: Generate charts (should not crash)
    figs = simulator.make_charts(df_bucket, df_global)

    # Verify charts were created
    assert len(figs) == 3  # Should return 3 base charts
    assert all(fig is not None for fig in figs)


def test_ui_workflow_with_invalid_inputs_tier2():
    """Test complete UI workflow with invalid inputs for Tier 2."""
    # Create config with invalid values
    config = {
        "token": {
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 24,
            "allocation_mode": "percent",
            "simulation_mode": "tier2"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "behaviors": {
            "cliff_shock": {"enabled": False},
            "price_trigger": {"enabled": False},
            "relock": {"enabled": False}
        },
        "tier2": {
            "staking": {
                "enabled": True,
                "apy": 0.15,
                "capacity": 0.60,
                "lockup": 6,
                "include_rewards": True
            },
            "pricing": {
                "enabled": True,
                "model": "bonding_curve",
                "initial_price": 1.0,
                "elasticity": 0.5
            },
            "treasury": {"enabled": False},
            "volume": {"enabled": False}
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 60,
                "tge_unlock_pct": 200,  # INVALID: way over 100%
                "cliff_months": -12,  # INVALID: negative
                "vesting_months": 12
            },
            {
                "bucket": "Investors",
                "allocation": 40,
                "tge_unlock_pct": -5,  # INVALID: negative
                "cliff_months": 6,
                "vesting_months": 12
            }
        ]
    }

    # Step 1: Validate
    warnings = validate_config(config)
    assert len(warnings) > 0

    # Step 2: Normalize
    config = normalize_config(config)

    # Verify normalization
    assert 0 <= config["buckets"][0]["tge_unlock_pct"] <= 100
    assert config["buckets"][0]["cliff_months"] >= 0
    assert 0 <= config["buckets"][1]["tge_unlock_pct"] <= 100

    # Step 3: Run simulation
    simulator = VestingSimulatorAdvanced(config, mode="tier2")
    df_bucket, df_global = simulator.run_simulation()

    # Verify simulation ran
    assert len(df_bucket) > 0
    assert len(df_global) > 0
    assert "current_price" in df_global.columns  # Tier 2 adds price

    # Step 4: Generate charts
    figs = simulator.make_charts(df_bucket, df_global)

    # Verify charts were created (Tier 2 may have more than 3)
    assert len(figs) >= 3
    assert all(fig is not None for fig in figs)


def test_ui_workflow_with_zero_supply():
    """Test UI workflow with zero supply (edge case)."""
    config = {
        "token": {
            "total_supply": 0,  # INVALID: zero supply
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
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": 100,
                "cliff_months": 0,
                "vesting_months": 0
            }
        ]
    }

    # Validate - should warn about zero supply
    warnings = validate_config(config)
    assert any("total_supply" in w for w in warnings)

    # Normalize
    config = normalize_config(config)

    # Run simulation - should handle zero supply gracefully
    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()

    assert len(df_global) > 0
    # With zero supply, all unlocks and sells should be zero
    assert df_global["total_unlocked"].sum() == 0


def test_ui_workflow_defensive_chart_access():
    """Test that UI can handle variable number of charts."""
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
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": 100,
                "cliff_months": 0,
                "vesting_months": 0
            }
        ]
    }

    config = normalize_config(config)
    simulator = VestingSimulator(config)
    df_bucket, df_global = simulator.run_simulation()
    figs = simulator.make_charts(df_bucket, df_global)

    # Simulate UI defensive chart access
    chart1 = figs[0] if len(figs) > 0 else None
    chart2 = figs[1] if len(figs) > 1 else None
    chart3 = figs[2] if len(figs) > 2 else None

    # Should not crash and should have all 3 charts
    assert chart1 is not None
    assert chart2 is not None
    assert chart3 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
