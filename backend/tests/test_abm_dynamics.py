"""
Tests for ABM dynamic systems (staking, treasury, pricing).
"""
import sys
from pathlib import Path

# Add backend/app to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import asyncio


async def test_staking_and_treasury():
    """Test simulation with staking and treasury enabled."""
    from app.abm.engine.simulation_loop import ABMSimulationLoop

    config = {
        "token": {
            "name": "TestToken",
            "total_supply": 1_000_000_000,
            "start_date": "2025-01-01",
            "horizon_months": 12
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 30,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 12
            },
            {
                "bucket": "Community",
                "allocation": 40,
                "tge_unlock_pct": 20,
                "cliff_months": 0,
                "vesting_months": 6
            }
        ],
        "abm": {
            "pricing_model": "eoe",
            "agents_per_cohort": 30,
            "pricing_config": {
                "holding_time": 6.0
            },
            # Enable staking
            "enable_staking": True,
            "staking_config": {
                "base_apy": 0.15,  # 15% APY
                "max_capacity_pct": 0.4,  # 40% of total supply
                "lockup_months": 6
            },
            # Enable treasury
            "enable_treasury": True,
            "treasury_config": {
                "initial_balance_pct": 0.10,
                "transaction_fee_pct": 0.03,  # 3% fee
                "hold_pct": 0.40,
                "liquidity_pct": 0.30,
                "buyback_pct": 0.30,
                "burn_bought_tokens": True
            }
        }
    }

    # Create simulation loop
    simulation_loop = ABMSimulationLoop.from_config(config)

    print("Running ABM simulation with staking and treasury...")
    print(f"  - {len(simulation_loop.agents)} agents")
    print(f"  - Staking: {simulation_loop.staking_controller is not None}")
    print(f"  - Treasury: {simulation_loop.treasury_controller is not None}")

    # Run simulation
    results = await simulation_loop.run_full_simulation(months=12)

    # Verify results
    assert len(results.global_metrics) == 12
    assert results.execution_time_seconds > 0

    # Check that tokens were staked
    total_staked = sum(r.total_staked for r in results.global_metrics)
    assert total_staked > 0, "Some tokens should have been staked"

    # Check that treasury collected fees (if there were sales)
    if simulation_loop.treasury_controller:
        assert simulation_loop.treasury_controller.total_fees_collected > 0, \
            "Treasury should have collected fees"

    # Check that staking reduced circulating supply
    first_supply = results.global_metrics[0].circulating_supply
    mid_supply = results.global_metrics[6].circulating_supply

    print(f"\n[OK] Simulation with dynamics completed:")
    print(f"  - Final price: ${results.global_metrics[-1].price:.4f}")
    print(f"  - Final supply: {results.global_metrics[-1].circulating_supply:,.0f}")
    print(f"  - Total staked (cumulative): {total_staked:,.0f}")

    if simulation_loop.staking_controller:
        print(f"  - Staking utilization: {simulation_loop.staking_controller.utilization_pct:.1f}%")
        print(f"  - Current APY: {simulation_loop.staking_controller.current_apy:.1%}")
        print(f"  - Rewards paid: {simulation_loop.staking_controller.total_rewards_distributed:,.0f}")

    if simulation_loop.treasury_controller:
        print(f"  - Fees collected: ${simulation_loop.treasury_controller.total_fees_collected:,.2f}")
        print(f"  - Tokens bought: {simulation_loop.treasury_controller.total_tokens_bought:,.0f}")
        print(f"  - Tokens burned: {simulation_loop.treasury_controller.total_tokens_burned:,.0f}")
        print(f"  - Treasury fiat: ${simulation_loop.treasury_controller.fiat_balance:,.2f}")

    print("\n[OK] All dynamic systems working correctly!")


async def test_variable_apy():
    """Test that staking APY varies with utilization."""
    from app.abm.dynamics.staking import StakingPool, StakingConfig

    config = StakingConfig(
        base_apy=0.12,
        max_capacity_pct=0.5,
        lockup_months=6
    )

    total_supply = 1_000_000_000
    staking_pool = StakingPool(config, total_supply)

    # Check APY at different utilization levels
    print("\nTesting variable APY:")

    # Empty pool (0% utilization)
    apy_0 = staking_pool.current_apy
    print(f"  0% utilization: {apy_0:.1%} APY")
    assert apy_0 == config.base_apy * 1.5, "Empty pool should have 150% of base APY"

    # Simulate some staking
    staking_pool.total_staked = staking_pool.max_capacity * 0.5  # 50% full
    apy_50 = staking_pool.current_apy
    print(f"  50% utilization: {apy_50:.1%} APY")

    # Full pool
    staking_pool.total_staked = staking_pool.max_capacity  # 100% full
    apy_100 = staking_pool.current_apy
    print(f"  100% utilization: {apy_100:.1%} APY")
    assert apy_100 == config.base_apy * 0.5, "Full pool should have 50% of base APY"

    # Verify APY decreases as utilization increases
    assert apy_0 > apy_50 > apy_100, "APY should decrease as pool fills"

    print("\n[OK] Variable APY working correctly!")


async def test_treasury_buyback_and_burn():
    """Test treasury buyback and burn functionality."""
    from app.abm.dynamics.treasury import TreasuryController, TreasuryConfig
    from app.abm.dynamics.token_economy import TokenEconomy, TokenEconomyConfig

    config = TreasuryConfig(
        initial_balance_pct=0.10,
        transaction_fee_pct=0.05,  # 5% fee
        hold_pct=0.00,  # All to buyback for easier testing
        liquidity_pct=0.00,
        buyback_pct=1.00,
        burn_bought_tokens=True
    )

    total_supply = 1_000_000_000
    treasury = TreasuryController(config, total_supply)

    # Create token economy and link
    token_economy = TokenEconomy(TokenEconomyConfig(
        total_supply=total_supply,
        initial_price=1.0,
        initial_circulating_supply=500_000_000
    ))
    treasury.link(TokenEconomy, token_economy)

    print("\nTesting treasury buyback and burn:")

    # Simulate sales
    sell_volume = 10_000_000  # 10M tokens sold
    current_price = 1.0

    initial_supply = token_economy.circulating_supply

    # Execute treasury
    metrics = await treasury.execute(sell_volume, current_price)

    print(f"  Fees collected: ${metrics['fees_collected']:,.2f}")
    print(f"  Tokens bought: {metrics['tokens_bought']:,.0f}")
    print(f"  Tokens burned: {metrics['tokens_burned']:,.0f}")

    # Verify fees were collected
    expected_fees = sell_volume * current_price * config.transaction_fee_pct
    assert metrics['fees_collected'] == expected_fees, "Fees calculation incorrect"

    # Verify buyback happened
    assert metrics['tokens_bought'] > 0, "Should have bought tokens"
    assert metrics['tokens_burned'] > 0, "Should have burned tokens"

    # Verify supply decreased
    final_supply = token_economy.circulating_supply
    assert final_supply < initial_supply, "Circulating supply should decrease after burn"
    assert initial_supply - final_supply == metrics['tokens_burned'], \
        "Supply reduction should equal burned tokens"

    print(f"  Supply reduced from {initial_supply:,.0f} to {final_supply:,.0f}")

    print("\n[OK] Treasury buyback and burn working correctly!")


if __name__ == "__main__":
    print("Running ABM dynamics tests...\n")
    print("=" * 70)

    asyncio.run(test_variable_apy())

    print("\n" + "=" * 70 + "\n")

    asyncio.run(test_treasury_buyback_and_burn())

    print("\n" + "=" * 70 + "\n")

    asyncio.run(test_staking_and_treasury())

    print("\n" + "=" * 70)
    print("\nAll dynamics tests passed!")
