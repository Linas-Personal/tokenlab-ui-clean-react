"""
Tests for Monte Carlo simulation engine.
"""
import sys
from pathlib import Path

# Add backend/app to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import asyncio
import time


async def test_monte_carlo_basic():
    """Test basic Monte Carlo simulation with small number of trials."""
    from app.abm.monte_carlo.parallel_mc import MonteCarloEngine

    config = {
        "token": {
            "name": "TestToken",
            "total_supply": 10_000_000,
            "start_date": "2025-01-01",
            "horizon_months": 6
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 30,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 6
            },
            {
                "bucket": "Community",
                "allocation": 50,
                "tge_unlock_pct": 20,
                "cliff_months": 0,
                "vesting_months": 3
            }
        ],
        "abm": {
            "pricing_model": "constant",
            "agent_granularity": "adaptive"
        }
    }

    print("\n" + "=" * 70)
    print("TEST: Basic Monte Carlo (10 trials)")
    print("=" * 70)

    mc_engine = MonteCarloEngine(
        num_trials=10,
        confidence_levels=[10, 50, 90],
        seed=42
    )

    start = time.time()
    results = await mc_engine.run_monte_carlo(config)
    elapsed = time.time() - start

    print(f"\n[OK] Monte Carlo completed:")
    print(f"  - Trials: {len(results.trials)}")
    print(f"  - Percentiles: {len(results.percentiles)} ({[p.percentile for p in results.percentiles]})")
    print(f"  - Mean trajectory months: {len(results.mean_metrics)}")
    print(f"  - Execution time: {elapsed:.2f}s ({elapsed/10:.3f}s/trial)")

    assert len(results.trials) == 10
    assert len(results.percentiles) == 3
    assert len(results.mean_metrics) == 6

    assert results.summary["num_trials"] == 10
    assert "mean_final_price" in results.summary
    assert "std_final_price" in results.summary
    assert "p10_final_price" in results.summary
    assert "p50_final_price" in results.summary
    assert "p90_final_price" in results.summary

    print(f"\n  Summary Statistics:")
    print(f"    - Mean final price: ${results.summary['mean_final_price']:.4f}")
    print(f"    - Std final price: ${results.summary['std_final_price']:.4f}")
    print(f"    - P10 final price: ${results.summary['p10_final_price']:.4f}")
    print(f"    - P50 final price: ${results.summary['p50_final_price']:.4f}")
    print(f"    - P90 final price: ${results.summary['p90_final_price']:.4f}")
    print(f"    - Coefficient of variation: {results.summary['coefficient_of_variation']:.4f}")

    print("\n[OK] Basic Monte Carlo test passed")


async def test_monte_carlo_percentiles():
    """Test that percentiles are correctly ordered and within bounds."""
    from app.abm.monte_carlo.parallel_mc import MonteCarloEngine

    config = {
        "token": {
            "name": "TestToken",
            "total_supply": 10_000_000,
            "start_date": "2025-01-01",
            "horizon_months": 12
        },
        "buckets": [
            {
                "bucket": "Community",
                "allocation": 50,
                "tge_unlock_pct": 25,
                "cliff_months": 0,
                "vesting_months": 6
            }
        ],
        "abm": {
            "pricing_model": "eoe",
            "agent_granularity": "adaptive"
        }
    }

    print("\n" + "=" * 70)
    print("TEST: Percentile Ordering and Bounds")
    print("=" * 70)

    mc_engine = MonteCarloEngine(num_trials=20, confidence_levels=[10, 50, 90], seed=123)

    results = await mc_engine.run_monte_carlo(config)

    p10_final_price = results.summary["p10_final_price"]
    p50_final_price = results.summary["p50_final_price"]
    p90_final_price = results.summary["p90_final_price"]

    print(f"\n  Final Price Percentiles:")
    print(f"    - P10: ${p10_final_price:.4f}")
    print(f"    - P50: ${p50_final_price:.4f}")
    print(f"    - P90: ${p90_final_price:.4f}")

    assert p10_final_price <= p50_final_price, "P10 should be <= P50"
    assert p50_final_price <= p90_final_price, "P50 should be <= P90"

    min_price = results.summary["min_final_price"]
    max_price = results.summary["max_final_price"]

    print(f"\n  Price Bounds:")
    print(f"    - Min: ${min_price:.4f}")
    print(f"    - Max: ${max_price:.4f}")

    assert p10_final_price >= min_price, "P10 should be >= min"
    assert p90_final_price <= max_price, "P90 should be <= max"

    print("\n[OK] Percentile ordering and bounds test passed")


async def test_monte_carlo_with_staking():
    """Test Monte Carlo with staking enabled."""
    from app.abm.monte_carlo.parallel_mc import MonteCarloEngine

    config = {
        "token": {
            "name": "StakingToken",
            "total_supply": 100_000_000,
            "start_date": "2025-01-01",
            "horizon_months": 12
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 20,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 12
            },
            {
                "bucket": "Community",
                "allocation": 40,
                "tge_unlock_pct": 25,
                "cliff_months": 0,
                "vesting_months": 6
            }
        ],
        "abm": {
            "pricing_model": "eoe",
            "agent_granularity": "adaptive",
            "enable_staking": True,
            "staking_config": {
                "base_apy": 0.15,
                "max_capacity_pct": 0.40,
                "lockup_months": 6,
                "reward_source": "emission"
            }
        }
    }

    print("\n" + "=" * 70)
    print("TEST: Monte Carlo with Staking")
    print("=" * 70)

    mc_engine = MonteCarloEngine(num_trials=15, seed=456)

    results = await mc_engine.run_monte_carlo(config)

    print(f"\n[OK] Monte Carlo with staking completed:")
    print(f"  - Trials: {len(results.trials)}")
    print(f"  - Mean final price: ${results.summary['mean_final_price']:.4f}")
    print(f"  - Std final price: ${results.summary['std_final_price']:.4f}")

    # Check that all trials completed successfully
    for trial in results.trials:
        assert len(trial.global_metrics) == 12, "Each trial should have 12 months"
        assert trial.final_price > 0, "Final price should be positive"

    print("\n[OK] Monte Carlo with staking test passed")


async def test_monte_carlo_with_treasury():
    """Test Monte Carlo with treasury enabled."""
    from app.abm.monte_carlo.parallel_mc import MonteCarloEngine

    config = {
        "token": {
            "name": "TreasuryToken",
            "total_supply": 100_000_000,
            "start_date": "2025-01-01",
            "horizon_months": 12
        },
        "buckets": [
            {
                "bucket": "VC",
                "allocation": 15,
                "tge_unlock_pct": 10,
                "cliff_months": 0,
                "vesting_months": 12
            },
            {
                "bucket": "Community",
                "allocation": 50,
                "tge_unlock_pct": 30,
                "cliff_months": 0,
                "vesting_months": 6
            }
        ],
        "abm": {
            "pricing_model": "eoe",
            "agent_granularity": "adaptive",
            "enable_treasury": True,
            "treasury_config": {
                "initial_balance_pct": 0.10,
                "transaction_fee_pct": 0.02,
                "hold_pct": 0.50,
                "liquidity_pct": 0.30,
                "buyback_pct": 0.20,
                "burn_bought_tokens": True
            }
        }
    }

    print("\n" + "=" * 70)
    print("TEST: Monte Carlo with Treasury")
    print("=" * 70)

    mc_engine = MonteCarloEngine(num_trials=15, seed=789)

    results = await mc_engine.run_monte_carlo(config)

    print(f"\n[OK] Monte Carlo with treasury completed:")
    print(f"  - Trials: {len(results.trials)}")
    print(f"  - Mean final price: ${results.summary['mean_final_price']:.4f}")
    print(f"  - Std final price: ${results.summary['std_final_price']:.4f}")

    for trial in results.trials:
        assert len(trial.global_metrics) == 12
        assert trial.final_price > 0

    print("\n[OK] Monte Carlo with treasury test passed")


async def test_monte_carlo_performance():
    """Benchmark Monte Carlo performance."""
    from app.abm.monte_carlo.parallel_mc import MonteCarloEngine

    config = {
        "token": {
            "name": "PerfTest",
            "total_supply": 10_000_000,
            "start_date": "2025-01-01",
            "horizon_months": 12
        },
        "buckets": [
            {
                "bucket": "Community",
                "allocation": 50,
                "tge_unlock_pct": 25,
                "cliff_months": 0,
                "vesting_months": 6
            }
        ],
        "abm": {
            "pricing_model": "constant",
            "agent_granularity": "adaptive"
        }
    }

    print("\n" + "=" * 70)
    print("PERFORMANCE BENCHMARK: Monte Carlo")
    print("=" * 70)

    test_cases = [
        {"name": "Small (10 trials)", "num_trials": 10},
        {"name": "Medium (50 trials)", "num_trials": 50},
        {"name": "Large (100 trials)", "num_trials": 100}
    ]

    for test in test_cases:
        mc_engine = MonteCarloEngine(num_trials=test["num_trials"], seed=1000)

        start = time.time()
        results = await mc_engine.run_monte_carlo(config)
        elapsed = time.time() - start

        print(f"\n{test['name']}:")
        print(f"  - Total time: {elapsed:.2f}s")
        print(f"  - Time per trial: {elapsed/test['num_trials']:.3f}s")
        print(f"  - Trials per second: {test['num_trials']/elapsed:.2f}")

        assert len(results.trials) == test["num_trials"]

        if test["num_trials"] <= 100:
            assert elapsed < 30.0, f"{test['name']} took too long ({elapsed:.2f}s)"

    print("\n[OK] Performance benchmark complete")


if __name__ == "__main__":
    print("Running Monte Carlo tests...\n")
    print("=" * 70)

    asyncio.run(test_monte_carlo_basic())

    print("\n" + "=" * 70)

    asyncio.run(test_monte_carlo_percentiles())

    print("\n" + "=" * 70)

    asyncio.run(test_monte_carlo_with_staking())

    print("\n" + "=" * 70)

    asyncio.run(test_monte_carlo_with_treasury())

    print("\n" + "=" * 70)

    asyncio.run(test_monte_carlo_performance())

    print("\n" + "=" * 70)
    print("\nAll Monte Carlo tests passed!")
