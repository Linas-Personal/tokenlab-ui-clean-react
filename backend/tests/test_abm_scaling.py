"""
Tests for ABM agent scaling system.
"""
import sys
from pathlib import Path

# Add backend/app to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import asyncio
import pytest
import time

@pytest.mark.anyio
async def test_scaling_strategy_selection():
    """Test that scaling strategy is selected correctly based on holder count."""
    from app.abm.agents.scaling import AdaptiveAgentScaling, ScalingStrategy

    scaling = AdaptiveAgentScaling()

    # Test thresholds
    assert scaling.determine_strategy(500) == ScalingStrategy.FULL_INDIVIDUAL
    assert scaling.determine_strategy(1000) == ScalingStrategy.FULL_INDIVIDUAL
    assert scaling.determine_strategy(5000) == ScalingStrategy.REPRESENTATIVE_SAMPLING
    assert scaling.determine_strategy(10000) == ScalingStrategy.REPRESENTATIVE_SAMPLING
    assert scaling.determine_strategy(50000) == ScalingStrategy.META_AGENTS
    assert scaling.determine_strategy(100000) == ScalingStrategy.META_AGENTS

    print("[OK] Strategy selection working correctly")

@pytest.mark.anyio
async def test_agent_count_calculation():
    """Test agent count calculation for different strategies."""
    from app.abm.agents.scaling import AdaptiveAgentScaling, ScalingStrategy

    scaling = AdaptiveAgentScaling()

    # Test case: 10K holders across 3 cohorts
    cohort_holder_counts = {
        "Team": 100,
        "VC": 400,
        "Community": 9500
    }

    # Full individual (1:1)
    result_full = scaling.calculate_agent_counts(
        cohort_holder_counts,
        ScalingStrategy.FULL_INDIVIDUAL
    )

    assert result_full["Team"][0] == 100
    assert result_full["Team"][1] == 1.0  # No scaling
    assert result_full["VC"][0] == 400
    assert result_full["Community"][0] == 9500

    print(f"Full individual: {sum(r[0] for r in result_full.values())} agents")

    # Representative sampling
    result_rep = scaling.calculate_agent_counts(
        cohort_holder_counts,
        ScalingStrategy.REPRESENTATIVE_SAMPLING
    )

    total_agents_rep = sum(r[0] for r in result_rep.values())
    assert total_agents_rep <= 1100  # Around 1000 sample size
    assert result_rep["Community"][1] > 1.0  # Should have scaling weight

    print(f"Representative: {total_agents_rep} agents (from 10K holders)")

    # Meta-agents
    result_meta = scaling.calculate_agent_counts(
        cohort_holder_counts,
        ScalingStrategy.META_AGENTS
    )

    assert result_meta["Team"][0] == 50  # Fixed 50 per cohort
    assert result_meta["VC"][0] == 50
    assert result_meta["Community"][0] == 50
    assert result_meta["Community"][1] == 9500 / 50  # Scaling weight = 190

    print(f"Meta-agents: {sum(r[0] for r in result_meta.values())} agents")

    print("\n[OK] Agent count calculation working correctly")

@pytest.mark.anyio
async def test_small_scale_simulation():
    """Test simulation with small supply (uses full individual if < 1K estimated holders)."""
    from app.abm.engine.simulation_loop import ABMSimulationLoop

    config = {
        "token": {
            "name": "SmallProject",
            "total_supply": 1_000_000,  # 1M tokens (smaller)
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
            "agent_granularity": "adaptive"  # Auto-detect
        }
    }

    print("\nTesting SMALL scale:")
    start = time.time()

    simulation_loop = ABMSimulationLoop.from_config(config)
    print(f"  Created {len(simulation_loop.agents)} agents")

    results = await simulation_loop.run_full_simulation(months=6)
    elapsed = time.time() - start

    print(f"  Execution time: {elapsed:.3f}s")
    print(f"  Time per iteration: {elapsed/6:.4f}s")

    assert len(results.global_metrics) == 6
    assert len(simulation_loop.agents) < 10000, "Should not create excessive agents"
    print("\n[OK] Small scale simulation complete")

@pytest.mark.anyio
async def test_medium_scale_simulation():
    """Test simulation with 1K-10K holders (representative sampling)."""
    from app.abm.engine.simulation_loop import ABMSimulationLoop

    config = {
        "token": {
            "name": "MediumProject",
            "total_supply": 1_000_000_000,  # 1B tokens
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
                "bucket": "VC",
                "allocation": 15,
                "tge_unlock_pct": 10,
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
            "agent_granularity": "adaptive"  # Auto-detect (should use sampling)
        }
    }

    print("\nTesting MEDIUM scale (1K-10K holders):")
    start = time.time()

    simulation_loop = ABMSimulationLoop.from_config(config)
    print(f"  Created {len(simulation_loop.agents)} agents (representative sampling)")

    results = await simulation_loop.run_full_simulation(months=12)
    elapsed = time.time() - start

    print(f"  Execution time: {elapsed:.3f}s")
    print(f"  Time per iteration: {elapsed/12:.4f}s")

    # Should use representative sampling or meta-agents (not full individual)
    assert len(simulation_loop.agents) < 5000, \
        "Should not create full individual agents for large supply"
    assert len(results.global_metrics) == 12

    print("\n[OK] Medium scale simulation complete")

@pytest.mark.anyio
async def test_large_scale_simulation():
    """Test simulation with > 10K holders (meta-agents)."""
    from app.abm.engine.simulation_loop import ABMSimulationLoop

    config = {
        "token": {
            "name": "LargeProject",
            "total_supply": 10_000_000_000,  # 10B tokens
            "start_date": "2025-01-01",
            "horizon_months": 24
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 15,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 24
            },
            {
                "bucket": "VC",
                "allocation": 10,
                "tge_unlock_pct": 10,
                "cliff_months": 0,
                "vesting_months": 18
            },
            {
                "bucket": "Investors",
                "allocation": 20,
                "tge_unlock_pct": 15,
                "cliff_months": 0,
                "vesting_months": 12
            },
            {
                "bucket": "Community",
                "allocation": 50,
                "tge_unlock_pct": 30,
                "cliff_months": 0,
                "vesting_months": 12
            }
        ],
        "abm": {
            "pricing_model": "eoe",
            "agent_granularity": "meta_agents"  # Force meta-agents
        }
    }

    print("\nTesting LARGE scale (> 10K holders):")
    start = time.time()

    simulation_loop = ABMSimulationLoop.from_config(config)
    print(f"  Created {len(simulation_loop.agents)} meta-agents")

    results = await simulation_loop.run_full_simulation(months=24)
    elapsed = time.time() - start

    print(f"  Execution time: {elapsed:.3f}s")
    print(f"  Time per iteration: {elapsed/24:.4f}s")

    # Should create 50 agents per cohort = 200 total
    assert len(simulation_loop.agents) == 200  # 4 cohorts * 50
    assert len(results.global_metrics) == 24

    # Verify scaling weights are applied
    sample_agent = simulation_loop.agents[0]
    assert sample_agent.attrs.scaling_weight > 1.0, \
        "Meta-agents should have scaling weight > 1"

    print(f"  Sample agent scaling weight: {sample_agent.attrs.scaling_weight:.1f}x")

    print("\n[OK] Large scale simulation complete")


async def benchmark_scaling_performance():
    """Benchmark performance across different scales."""
    from app.abm.engine.simulation_loop import ABMSimulationLoop

    print("\n" + "=" * 70)
    print("PERFORMANCE BENCHMARK")
    print("=" * 70)

    test_cases = [
        {
            "name": "Small (100 holders)",
            "total_supply": 1_000_000,
            "allocation": 30,
            "months": 12,
            "granularity": "full_individual"
        },
        {
            "name": "Medium (10K holders)",
            "total_supply": 1_000_000_000,
            "allocation": 40,
            "months": 12,
            "granularity": "adaptive"
        },
        {
            "name": "Large (100K holders)",
            "total_supply": 10_000_000_000,
            "allocation": 50,
            "months": 12,
            "granularity": "meta_agents"
        },
        {
            "name": "Extra Large (1M holders)",
            "total_supply": 100_000_000_000,
            "allocation": 50,
            "months": 12,
            "granularity": "meta_agents"
        }
    ]

    results = []

    for test in test_cases:
        config = {
            "token": {
                "name": test["name"],
                "total_supply": test["total_supply"],
                "start_date": "2025-01-01",
                "horizon_months": test["months"]
            },
            "buckets": [
                {
                    "bucket": "Community",
                    "allocation": test["allocation"],
                    "tge_unlock_pct": 20,
                    "cliff_months": 0,
                    "vesting_months": 6
                }
            ],
            "abm": {
                "pricing_model": "constant",
                "agent_granularity": test["granularity"]
            }
        }

        start = time.time()
        sim_loop = ABMSimulationLoop.from_config(config)
        sim_results = await sim_loop.run_full_simulation(months=test["months"])
        elapsed = time.time() - start

        results.append({
            "name": test["name"],
            "agents": len(sim_loop.agents),
            "months": test["months"],
            "total_time": elapsed,
            "time_per_month": elapsed / test["months"]
        })

    # Print benchmark results
    print(f"\n{'Project Size':<25} {'Agents':<10} {'Months':<8} {'Total':<10} {'Per Month':<12}")
    print("-" * 70)

    for r in results:
        print(
            f"{r['name']:<25} {r['agents']:<10} {r['months']:<8} "
            f"{r['total_time']:>7.3f}s   {r['time_per_month']:>9.4f}s"
        )

    print("=" * 70)

    # Performance assertions
    for r in results:
        # All should complete in reasonable time
        assert r['total_time'] < 30.0, f"{r['name']} took too long"

        # Per-month should be fast regardless of scale
        assert r['time_per_month'] < 2.0, f"{r['name']} per-month time too slow"

    print("\n[OK] Performance benchmark complete - all targets met!")

@pytest.mark.anyio
async def test_performance_estimates():
    """Test performance estimation function."""
    from app.abm.agents.scaling import AdaptiveAgentScaling

    print("\n" + "=" * 70)
    print("PERFORMANCE ESTIMATES")
    print("=" * 70)

    test_scales = [100, 1000, 10000, 100000, 1000000]

    print(f"\n{'Holders':<12} {'Strategy':<25} {'Agents':<10} {'Est. Time (36m)':<20}")
    print("-" * 70)

    for holders in test_scales:
        estimates = AdaptiveAgentScaling.estimate_performance(holders, 36)

        print(
            f"{holders:>10,}  {estimates['strategy']:<25} "
            f"{estimates['estimated_agents']:<10} {estimates['total_time_sec']:>10.3f}s"
        )

    print("=" * 70)
    print("\n[OK] Performance estimates calculated")


if __name__ == "__main__":
    print("Running ABM scaling tests...\n")
    print("=" * 70)

    asyncio.run(test_scaling_strategy_selection())

    print("\n" + "=" * 70)

    asyncio.run(test_agent_count_calculation())

    print("\n" + "=" * 70)

    asyncio.run(test_small_scale_simulation())

    print("\n" + "=" * 70)

    asyncio.run(test_medium_scale_simulation())

    print("\n" + "=" * 70)

    asyncio.run(test_large_scale_simulation())

    print("\n" + "=" * 70)

    asyncio.run(test_performance_estimates())

    print("\n" + "=" * 70)

    asyncio.run(benchmark_scaling_performance())

    print("\n" + "=" * 70)
    print("\nAll scaling tests passed!")
