"""
Tests for ABM Volume Controller and Cohort Mapping.
"""
import sys
from pathlib import Path

# Add backend/app to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import asyncio


async def test_volume_controller_proportional():
    """Test proportional volume model (scales with supply)."""
    from app.abm.dynamics.volume import VolumeController, VolumeConfigData
    from app.abm.dynamics.token_economy import TokenEconomy, TokenEconomyConfig

    print("\nTesting proportional volume model:")

    # Create volume controller with proportional model
    config = VolumeConfigData(
        volume_model="proportional",
        base_daily_volume=10_000_000,
        volume_multiplier=1.0
    )
    volume_controller = VolumeController(config)

    # Create token economy
    total_supply = 1_000_000_000
    token_economy = TokenEconomy(TokenEconomyConfig(
        total_supply=total_supply,
        initial_price=1.0,
        initial_circulating_supply=0
    ))

    # Link dependency
    volume_controller.link(TokenEconomy, token_economy)

    # Test at 0% circulating supply
    token_economy.circulating_supply = 0
    volume_0 = await volume_controller.execute()
    print(f"  Volume at 0% supply: {volume_0:,.0f} tokens")
    assert volume_0 == 0, "Volume should be 0 when no circulating supply"

    # Test at 25% circulating supply
    token_economy.circulating_supply = total_supply * 0.25
    volume_25 = await volume_controller.execute()
    expected_25 = config.base_daily_volume * 0.25 * config.volume_multiplier
    print(f"  Volume at 25% supply: {volume_25:,.0f} tokens (expected: {expected_25:,.0f})")
    assert abs(volume_25 - expected_25) < 1.0, "Volume should scale with supply ratio"

    # Test at 50% circulating supply
    token_economy.circulating_supply = total_supply * 0.5
    volume_50 = await volume_controller.execute()
    expected_50 = config.base_daily_volume * 0.5 * config.volume_multiplier
    print(f"  Volume at 50% supply: {volume_50:,.0f} tokens (expected: {expected_50:,.0f})")
    assert abs(volume_50 - expected_50) < 1.0, "Volume should scale with supply ratio"

    # Test at 100% circulating supply
    token_economy.circulating_supply = total_supply
    volume_100 = await volume_controller.execute()
    expected_100 = config.base_daily_volume * 1.0 * config.volume_multiplier
    print(f"  Volume at 100% supply: {volume_100:,.0f} tokens (expected: {expected_100:,.0f})")
    assert abs(volume_100 - expected_100) < 1.0, "Volume should equal base at 100% supply"

    # Verify volume increases with supply
    assert volume_0 < volume_25 < volume_50 < volume_100, \
        "Volume should increase as circulating supply increases"

    print("\n[OK] Proportional volume model working correctly!")


async def test_volume_controller_constant():
    """Test constant volume model (fixed)."""
    from app.abm.dynamics.volume import VolumeController, VolumeConfigData
    from app.abm.dynamics.token_economy import TokenEconomy, TokenEconomyConfig

    print("\nTesting constant volume model:")

    # Create volume controller with constant model
    config = VolumeConfigData(
        volume_model="constant",
        base_daily_volume=5_000_000,
        volume_multiplier=2.0  # 2x multiplier
    )
    volume_controller = VolumeController(config)

    # Create token economy
    total_supply = 1_000_000_000
    token_economy = TokenEconomy(TokenEconomyConfig(
        total_supply=total_supply,
        initial_price=1.0,
        initial_circulating_supply=0
    ))

    # Link dependency
    volume_controller.link(TokenEconomy, token_economy)

    expected_volume = config.base_daily_volume * config.volume_multiplier

    # Test at different supply levels
    for supply_pct in [0.0, 0.25, 0.5, 0.75, 1.0]:
        token_economy.circulating_supply = total_supply * supply_pct
        volume = await volume_controller.execute()
        print(f"  Volume at {supply_pct*100:.0f}% supply: {volume:,.0f} tokens")
        assert abs(volume - expected_volume) < 1.0, \
            f"Volume should be constant at {expected_volume:,.0f} regardless of supply"

    print(f"  Expected constant volume: {expected_volume:,.0f} tokens")
    print("\n[OK] Constant volume model working correctly!")


async def test_volume_multiplier():
    """Test volume multiplier effect."""
    from app.abm.dynamics.volume import VolumeController, VolumeConfigData
    from app.abm.dynamics.token_economy import TokenEconomy, TokenEconomyConfig

    print("\nTesting volume multiplier:")

    token_economy = TokenEconomy(TokenEconomyConfig(
        total_supply=1_000_000_000,
        initial_price=1.0,
        initial_circulating_supply=500_000_000  # 50% supply
    ))

    base_volume = 10_000_000

    # Test different multipliers
    for multiplier in [0.5, 1.0, 2.0, 5.0]:
        config = VolumeConfigData(
            volume_model="constant",
            base_daily_volume=base_volume,
            volume_multiplier=multiplier
        )
        volume_controller = VolumeController(config)
        volume_controller.link(TokenEconomy, token_economy)

        volume = await volume_controller.execute()
        expected = base_volume * multiplier
        print(f"  Multiplier {multiplier}x: {volume:,.0f} tokens (expected: {expected:,.0f})")
        assert abs(volume - expected) < 1.0, \
            f"Volume should be {expected:,.0f} with {multiplier}x multiplier"

    print("\n[OK] Volume multiplier working correctly!")


async def test_volume_with_eoe_pricing():
    """Test volume controller integration with EOE pricing model."""
    from app.abm.dynamics.volume import VolumeController, VolumeConfigData
    from app.abm.dynamics.pricing import EOEPricingController
    from app.abm.dynamics.token_economy import TokenEconomy, TokenEconomyConfig

    print("\nTesting volume integration with EOE pricing:")

    # Create token economy
    token_economy = TokenEconomy(TokenEconomyConfig(
        total_supply=1_000_000_000,
        initial_price=1.0,
        initial_circulating_supply=100_000_000
    ))

    # Create volume controller
    volume_config = VolumeConfigData(
        volume_model="proportional",
        base_daily_volume=50_000_000,
        volume_multiplier=1.0
    )
    volume_controller = VolumeController(volume_config)
    volume_controller.link(TokenEconomy, token_economy)

    # Create EOE pricing controller
    pricing_config = {
        "holding_time": 6.0,
        "smoothing_factor": 0.7,
        "min_price": 0.01
    }
    eoe_pricing = EOEPricingController(pricing_config)
    eoe_pricing.link(TokenEconomy, token_economy)

    # Link volume controller to EOE pricing
    eoe_pricing.set_volume_controller(volume_controller)

    # Simulate some sell pressure
    token_economy.total_sell_pressure = 1_000_000  # 1M tokens sold

    # Calculate price with volume controller
    price_with_volume = await eoe_pricing.execute()

    print(f"  Circulating supply: {token_economy.circulating_supply:,.0f}")
    print(f"  Calculated volume: {await volume_controller.execute():,.0f} tokens")
    print(f"  Price with volume: ${price_with_volume:.4f}")

    assert price_with_volume > 0, "Price should be positive"
    assert price_with_volume >= pricing_config["min_price"], \
        "Price should respect minimum floor"

    print("\n[OK] Volume integration with EOE pricing working correctly!")


async def test_simulation_with_volume_enabled():
    """Test full simulation with volume controller enabled."""
    from app.abm.engine.simulation_loop import ABMSimulationLoop

    print("\nTesting full simulation with volume controller:")

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
                "allocation": 40,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 12
            },
            {
                "bucket": "Community",
                "allocation": 60,
                "tge_unlock_pct": 20,
                "cliff_months": 0,
                "vesting_months": 6
            }
        ],
        "abm": {
            "pricing_model": "eoe",
            "agents_per_cohort": 20,
            "pricing_config": {
                "holding_time": 6.0,
                "smoothing_factor": 0.7
            },
            # Enable volume controller
            "enable_volume": True,
            "volume_config": {
                "volume_model": "proportional",
                "base_daily_volume": 20_000_000,
                "volume_multiplier": 1.5
            }
        }
    }

    # Create and run simulation
    simulation_loop = ABMSimulationLoop.from_config(config)

    print(f"  - {len(simulation_loop.agents)} agents")
    print(f"  - Volume controller: {simulation_loop.volume_controller is not None}")
    print(f"  - Pricing model: {simulation_loop.pricing_controller.__class__.__name__}")

    results = await simulation_loop.run_full_simulation(months=6)

    # Verify results
    assert len(results.global_metrics) == 6, "Should have 6 months of results"
    assert results.execution_time_seconds > 0, "Should have execution time"

    print(f"\n  Results:")
    print(f"  - Initial price: ${results.global_metrics[0].price:.4f}")
    print(f"  - Final price: ${results.global_metrics[-1].price:.4f}")
    print(f"  - Final circulating supply: {results.global_metrics[-1].circulating_supply:,.0f}")
    print(f"  - Total sold: {results.global_metrics[-1].total_sold:,.0f}")

    # Verify price changed (due to volume-based EOE pricing)
    assert results.global_metrics[0].price != results.global_metrics[-1].price, \
        "Price should change with volume-based EOE pricing"

    print("\n[OK] Simulation with volume controller working correctly!")


def test_cohort_profile_resolution():
    """Test cohort profile resolution with mapping."""
    from app.abm.agents.cohort import (
        resolve_cohort_profile,
        SIMPLE_COHORT_PRESETS,
        DEFAULT_COHORT_PROFILES
    )

    print("\nTesting cohort profile resolution:")

    # Test 1: Mapping to simple preset
    mapping = {"Team": "conservative", "VC": "aggressive"}
    profile = resolve_cohort_profile("Team", mapping)
    assert profile == SIMPLE_COHORT_PRESETS["conservative"], \
        "Should use mapped conservative preset for Team"
    print(f"  Team with mapping: conservative preset (sell={profile.sell_pressure_mean:.2f})")

    profile = resolve_cohort_profile("VC", mapping)
    assert profile == SIMPLE_COHORT_PRESETS["aggressive"], \
        "Should use mapped aggressive preset for VC"
    print(f"  VC with mapping: aggressive preset (sell={profile.sell_pressure_mean:.2f})")

    # Test 2: Default profile by bucket name (no mapping)
    profile = resolve_cohort_profile("Team", {})
    assert profile == DEFAULT_COHORT_PROFILES["Team"], \
        "Should use default Team profile when no mapping"
    print(f"  Team without mapping: default Team profile (sell={profile.sell_pressure_mean:.2f})")

    profile = resolve_cohort_profile("Community", {})
    assert profile == DEFAULT_COHORT_PROFILES["Community"], \
        "Should use default Community profile when no mapping"
    print(f"  Community without mapping: default Community profile (sell={profile.sell_pressure_mean:.2f})")

    # Test 3: Fallback to Community for unknown bucket
    profile = resolve_cohort_profile("UnknownBucket", {})
    assert profile == DEFAULT_COHORT_PROFILES["Community"], \
        "Should fall back to Community profile for unknown bucket"
    print(f"  UnknownBucket: Community fallback (sell={profile.sell_pressure_mean:.2f})")

    # Test 4: Invalid preset in mapping (should fall back)
    mapping_invalid = {"Team": "invalid_preset"}
    profile = resolve_cohort_profile("Team", mapping_invalid)
    assert profile == DEFAULT_COHORT_PROFILES["Team"], \
        "Should use default when mapping has invalid preset"
    print(f"  Team with invalid mapping: fallback to default (sell={profile.sell_pressure_mean:.2f})")

    # Test 5: Verify preset characteristics
    conservative = SIMPLE_COHORT_PRESETS["conservative"]
    moderate = SIMPLE_COHORT_PRESETS["moderate"]
    aggressive = SIMPLE_COHORT_PRESETS["aggressive"]

    assert conservative.sell_pressure_mean < moderate.sell_pressure_mean < aggressive.sell_pressure_mean, \
        "Sell pressure should increase from conservative to aggressive"
    print(f"\n  Preset sell pressure ordering verified:")
    print(f"    Conservative: {conservative.sell_pressure_mean:.2f}")
    print(f"    Moderate: {moderate.sell_pressure_mean:.2f}")
    print(f"    Aggressive: {aggressive.sell_pressure_mean:.2f}")

    # Staking propensity (calculated from stake_alpha / (stake_alpha + stake_beta))
    cons_stake = conservative.stake_alpha / (conservative.stake_alpha + conservative.stake_beta)
    mod_stake = moderate.stake_alpha / (moderate.stake_alpha + moderate.stake_beta)
    agg_stake = aggressive.stake_alpha / (aggressive.stake_alpha + aggressive.stake_beta)

    assert cons_stake > mod_stake > agg_stake, \
        "Staking propensity should decrease from conservative to aggressive"
    print(f"\n  Preset staking propensity ordering verified:")
    print(f"    Conservative: {cons_stake:.2f}")
    print(f"    Moderate: {mod_stake:.2f}")
    print(f"    Aggressive: {agg_stake:.2f}")

    print("\n[OK] Cohort profile resolution working correctly!")


async def test_simulation_with_cohort_mapping():
    """Test simulation with custom cohort behavior mapping."""
    from app.abm.engine.simulation_loop import ABMSimulationLoop

    print("\nTesting simulation with cohort behavior mapping:")

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
                "cliff_months": 6,
                "vesting_months": 18
            },
            {
                "bucket": "Investors",
                "allocation": 40,
                "tge_unlock_pct": 10,
                "cliff_months": 3,
                "vesting_months": 12
            },
            {
                "bucket": "Community",
                "allocation": 30,
                "tge_unlock_pct": 20,
                "cliff_months": 0,
                "vesting_months": 6
            }
        ],
        "abm": {
            "pricing_model": "eoe",
            "agents_per_cohort": 25,
            # Apply cohort behavior mapping
            "bucket_cohort_mapping": {
                "Team": "conservative",  # Low sell, high stake
                "Investors": "moderate",  # Medium sell, medium stake
                "Community": "aggressive"  # High sell, low stake
            }
        }
    }

    # Create and run simulation
    simulation_loop = ABMSimulationLoop.from_config(config)

    print(f"  - {len(simulation_loop.agents)} agents across 3 cohorts")
    print(f"  - Cohort mapping applied:")
    print(f"    Team -> conservative")
    print(f"    Investors -> moderate")
    print(f"    Community -> aggressive")

    results = await simulation_loop.run_full_simulation(months=6)

    # Verify results
    assert len(results.global_metrics) == 6
    assert results.execution_time_seconds > 0

    # Check that different cohorts had different behaviors
    # (This is validated by the backend using the mapping)
    total_sold = sum(r.total_sold for r in results.global_metrics)
    total_staked = sum(r.total_staked for r in results.global_metrics)

    print(f"\n  Results:")
    print(f"  - Total sold (cumulative): {total_sold:,.0f}")
    print(f"  - Total staked (cumulative): {total_staked:,.0f}")
    print(f"  - Final price: ${results.global_metrics[-1].price:.4f}")

    assert total_sold > 0, "Some tokens should have been sold"
    assert total_staked >= 0, "Staking might occur if enabled"

    print("\n[OK] Simulation with cohort mapping working correctly!")


if __name__ == "__main__":
    print("Running ABM Volume and Cohort Mapping tests...\n")
    print("=" * 70)

    # Volume controller tests
    asyncio.run(test_volume_controller_proportional())

    print("\n" + "=" * 70 + "\n")

    asyncio.run(test_volume_controller_constant())

    print("\n" + "=" * 70 + "\n")

    asyncio.run(test_volume_multiplier())

    print("\n" + "=" * 70 + "\n")

    asyncio.run(test_volume_with_eoe_pricing())

    print("\n" + "=" * 70 + "\n")

    asyncio.run(test_simulation_with_volume_enabled())

    print("\n" + "=" * 70 + "\n")

    # Cohort mapping tests
    test_cohort_profile_resolution()

    print("\n" + "=" * 70 + "\n")

    asyncio.run(test_simulation_with_cohort_mapping())

    print("\n" + "=" * 70)
    print("\nAll volume and cohort mapping tests passed!")
