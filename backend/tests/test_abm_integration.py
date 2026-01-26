"""
Integration tests for ABM simulation system.
"""
import sys
from pathlib import Path

# Add backend/app to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import pytest
import asyncio
from datetime import datetime


@pytest.mark.asyncio
async def test_abm_simulation_basic():
    """Test basic ABM simulation with 3 cohorts."""
    from app.abm.engine.simulation_loop import ABMSimulationLoop
    from app.abm.agents.cohort import AgentCohort, DEFAULT_COHORT_PROFILES
    from app.abm.dynamics.token_economy import TokenEconomy, TokenEconomyConfig
    from app.abm.dynamics.pricing import EOEPricingController

    # Create token economy
    token_economy = TokenEconomy(TokenEconomyConfig(
        total_supply=1_000_000_000,
        initial_price=1.0,
        initial_circulating_supply=0.0
    ))

    # Create agents from cohorts
    all_agents = []

    # Team cohort
    team_cohort = AgentCohort("Team", DEFAULT_COHORT_PROFILES["Team"], seed=42)
    team_config = {
        "bucket": "Team",
        "allocation": 20,
        "tge_unlock_pct": 0,
        "cliff_months": 12,
        "vesting_months": 24
    }
    team_agents = team_cohort.create_agents(
        num_agents=10,
        total_allocation=200_000_000,
        vesting_config=team_config
    )
    all_agents.extend(team_agents)

    # VC cohort
    vc_cohort = AgentCohort("VC", DEFAULT_COHORT_PROFILES["VC"], seed=42)
    vc_config = {
        "bucket": "VC",
        "allocation": 15,
        "tge_unlock_pct": 10,
        "cliff_months": 6,
        "vesting_months": 18
    }
    vc_agents = vc_cohort.create_agents(
        num_agents=10,
        total_allocation=150_000_000,
        vesting_config=vc_config
    )
    all_agents.extend(vc_agents)

    # Community cohort
    community_cohort = AgentCohort("Community", DEFAULT_COHORT_PROFILES["Community"], seed=42)
    community_config = {
        "bucket": "Community",
        "allocation": 40,
        "tge_unlock_pct": 20,
        "cliff_months": 0,
        "vesting_months": 12
    }
    community_agents = community_cohort.create_agents(
        num_agents=10,
        total_allocation=400_000_000,
        vesting_config=community_config
    )
    all_agents.extend(community_agents)

    # Create pricing controller
    pricing_controller = EOEPricingController({
        "holding_time": 6.0,
        "smoothing_factor": 0.7
    })

    # Create simulation loop
    simulation_loop = ABMSimulationLoop(
        agents=all_agents,
        token_economy=token_economy,
        pricing_controller=pricing_controller,
        start_date=datetime(2025, 1, 1)
    )

    # Run simulation for 12 months
    results = await simulation_loop.run_full_simulation(months=12)

    # Assertions
    assert len(results.global_metrics) == 12
    assert results.execution_time_seconds > 0

    # Check that price changes over time (feedback loop working)
    prices = [r.price for r in results.global_metrics]
    assert len(set(prices)) > 1, "Price should change over time"

    # Check that circulating supply increases
    first_supply = results.global_metrics[0].circulating_supply
    last_supply = results.global_metrics[-1].circulating_supply
    assert last_supply > first_supply, "Circulating supply should increase"

    # Check that tokens are being sold
    total_sold = sum(r.total_sold for r in results.global_metrics)
    assert total_sold > 0, "Tokens should be sold"

    print(f"[OK] ABM simulation completed successfully:")
    print(f"  - {len(all_agents)} agents")
    print(f"  - {len(results.global_metrics)} months")
    print(f"  - Final price: ${results.global_metrics[-1].price:.4f}")
    print(f"  - Final supply: {results.global_metrics[-1].circulating_supply:,.0f}")
    print(f"  - Total sold: {total_sold:,.0f}")
    print(f"  - Execution time: {results.execution_time_seconds:.2f}s")


@pytest.mark.asyncio
async def test_abm_from_config():
    """Test creating ABM simulation from config dict."""
    from app.abm.engine.simulation_loop import ABMSimulationLoop

    config = {
        "token": {
            "name": "TestToken",
            "total_supply": 1_000_000_000,
            "start_date": "2025-01-01",
            "horizon_months": 6
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 30,
                "tge_unlock_pct": 0,
                "cliff_months": 12,
                "vesting_months": 24
            },
            {
                "bucket": "Community",
                "allocation": 40,
                "tge_unlock_pct": 20,
                "cliff_months": 0,
                "vesting_months": 12
            }
        ],
        "abm": {
            "pricing_model": "eoe",
            "agents_per_cohort": 20,
            "pricing_config": {
                "holding_time": 6.0
            }
        }
    }

    # Create simulation loop from config
    simulation_loop = ABMSimulationLoop.from_config(config)

    # Run simulation
    results = await simulation_loop.run_full_simulation(months=6)

    # Assertions
    assert len(results.global_metrics) == 6
    assert len(simulation_loop.agents) == 40  # 2 cohorts * 20 agents

    print(f"[OK] ABM from config completed successfully:")
    print(f"  - {len(simulation_loop.agents)} agents")
    print(f"  - Final price: ${results.global_metrics[-1].price:.4f}")


if __name__ == "__main__":
    # Run tests directly
    print("Running ABM integration tests...")
    asyncio.run(test_abm_simulation_basic())
    asyncio.run(test_abm_from_config())
    print("\nAll tests passed!")
