"""
Configuration migration utilities for backward compatibility.

Handles migration of legacy tier1/tier2/tier3 configurations to ABM format.
"""
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


def migrate_legacy_config(config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Migrate legacy configuration to ABM format.

    Args:
        config: Configuration dict (may have simulation_mode: tier1/tier2/tier3)

    Returns:
        Tuple of (migrated_config, warnings)
            - migrated_config: Updated config with ABM settings
            - warnings: List of migration warning messages

    Examples:
        >>> config = {"token": {"simulation_mode": "tier2"}, ...}
        >>> migrated, warnings = migrate_legacy_config(config)
        >>> migrated["token"]["simulation_mode"]
        'abm'
    """
    warnings = []
    migrated = config.copy()

    # Extract simulation mode
    simulation_mode = config.get("token", {}).get("simulation_mode", "abm")

    if simulation_mode == "abm":
        # Already ABM, no migration needed
        return migrated, warnings

    # Detect legacy mode
    if simulation_mode in ["tier1", "tier2", "tier3"]:
        logger.info(f"Migrating legacy config from {simulation_mode} to ABM")
        warnings.append(
            f"Legacy simulation mode '{simulation_mode}' detected. "
            f"Migrating to ABM (Agent-Based Model) format."
        )

        # Update simulation mode to ABM
        if "token" not in migrated:
            migrated["token"] = {}
        migrated["token"]["simulation_mode"] = "abm"

        # Ensure ABM config exists
        if "abm" not in migrated:
            migrated["abm"] = {}

        # Migrate tier-specific features to ABM
        if simulation_mode == "tier2":
            _migrate_tier2_to_abm(migrated, warnings)
        elif simulation_mode == "tier3":
            _migrate_tier3_to_abm(migrated, warnings)

        # tier1 is basic vesting only, maps directly to ABM with minimal config
        if simulation_mode == "tier1":
            warnings.append(
                "Tier 1 (basic vesting) migrated to ABM with default agent behaviors. "
                "Consider customizing agent parameters for more realistic market dynamics."
            )

    return migrated, warnings


def _migrate_tier2_to_abm(config: Dict[str, Any], warnings: List[str]) -> None:
    """
    Migrate Tier 2 features to ABM configuration.

    Tier 2 includes: staking, pricing models, treasury, volume.

    Args:
        config: Configuration dict (modified in-place)
        warnings: Warning list (modified in-place)
    """
    tier2_config = config.get("tier2", {})

    # Migrate staking configuration
    if tier2_config.get("staking", {}).get("enabled", False):
        staking_config = tier2_config["staking"]
        config["abm"]["enable_staking"] = True
        config["abm"]["staking_config"] = {
            "base_apy": staking_config.get("apy", 0.12),
            "max_capacity_pct": staking_config.get("max_capacity_pct", 0.5),
            "lockup_months": staking_config.get("lockup_months", 6),
            "reward_source": staking_config.get("reward_source", "treasury"),
            "apy_multiplier_at_empty": 1.5,
            "apy_multiplier_at_full": 0.5
        }
        warnings.append("Tier 2 staking configuration migrated to ABM staking pool.")

    # Migrate pricing configuration
    if tier2_config.get("pricing", {}).get("enabled", False):
        pricing_config = tier2_config["pricing"]
        pricing_model = pricing_config.get("pricing_model", "bonding_curve")

        # Map tier2 pricing models to ABM pricing models
        pricing_model_map = {
            "bonding_curve": "bonding_curve",
            "constant": "constant"
        }
        config["abm"]["pricing_model"] = pricing_model_map.get(pricing_model, "eoe")

        if pricing_model == "bonding_curve":
            config["abm"]["pricing_config"] = {
                "k": pricing_config.get("bonding_curve_param", 0.000001),
                "n": 2.0
            }
        elif pricing_model == "constant":
            config["abm"]["initial_price"] = pricing_config.get("initial_price", 1.0)

        warnings.append(f"Tier 2 pricing model '{pricing_model}' migrated to ABM pricing.")

    # Migrate treasury configuration
    if tier2_config.get("treasury", {}).get("enabled", False):
        treasury_config = tier2_config["treasury"]
        config["abm"]["enable_treasury"] = True
        config["abm"]["treasury_config"] = {
            "initial_balance_pct": treasury_config.get("initial_balance_pct", 0.15),
            "transaction_fee_pct": 0.02,  # Default for ABM
            "hold_pct": treasury_config.get("hold_pct", 0.5),
            "liquidity_pct": treasury_config.get("liquidity_pct", 0.3),
            "buyback_pct": treasury_config.get("buyback_pct", 0.2),
            "burn_bought_tokens": True
        }
        warnings.append("Tier 2 treasury configuration migrated to ABM treasury controller.")

    # Migrate volume configuration
    if tier2_config.get("volume", {}).get("enabled", False):
        volume_config = tier2_config["volume"]
        config["abm"]["enable_volume"] = True
        config["abm"]["volume_config"] = {
            "volume_model": volume_config.get("volume_model", "proportional"),
            "base_daily_volume": volume_config.get("base_daily_volume", 10_000_000),
            "volume_multiplier": volume_config.get("volume_multiplier", 1.0)
        }
        warnings.append("Tier 2 volume configuration migrated to ABM dynamic volume.")


def _migrate_tier3_to_abm(config: Dict[str, Any], warnings: List[str]) -> None:
    """
    Migrate Tier 3 features to ABM configuration.

    Tier 3 includes: Monte Carlo simulations, cohort behavior.

    Args:
        config: Configuration dict (modified in-place)
        warnings: Warning list (modified in-place)
    """
    # First migrate tier2 features (tier3 includes tier2)
    _migrate_tier2_to_abm(config, warnings)

    tier3_config = config.get("tier3", {})

    # Migrate Monte Carlo configuration
    if tier3_config.get("monte_carlo", {}).get("enabled", False):
        mc_config = tier3_config["monte_carlo"]
        config["monte_carlo"] = {
            "enabled": True,
            "num_trials": mc_config.get("num_trials", 100),
            "variance_level": mc_config.get("variance_level", "medium"),
            "seed": mc_config.get("seed"),
            "confidence_levels": [10, 50, 90]
        }
        warnings.append("Tier 3 Monte Carlo configuration migrated to ABM Monte Carlo.")

    # Migrate cohort behavior configuration
    if tier3_config.get("cohort_behavior", {}).get("enabled", False):
        cohort_config = tier3_config["cohort_behavior"]
        bucket_mapping = cohort_config.get("bucket_cohort_mapping", {})

        # Convert tier3 cohort profiles to ABM simple presets if applicable
        # tier3 used: high_stake, high_sell, balanced
        # ABM uses: conservative, moderate, aggressive
        profile_map = {
            "high_stake": "conservative",
            "high_sell": "aggressive",
            "balanced": "moderate"
        }

        migrated_mapping = {}
        for bucket, profile in bucket_mapping.items():
            migrated_profile = profile_map.get(profile, profile)
            migrated_mapping[bucket] = migrated_profile

        config["abm"]["bucket_cohort_mapping"] = migrated_mapping
        warnings.append(
            f"Tier 3 cohort behavior migrated to ABM cohort mapping. "
            f"{len(migrated_mapping)} bucket assignments converted."
        )


def validate_migrated_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate migrated configuration and generate recommendations.

    Args:
        config: Migrated configuration dict

    Returns:
        List of validation warnings/recommendations
    """
    recommendations = []

    abm_config = config.get("abm", {})

    # Check if using default ABM settings after migration
    if not abm_config.get("enable_staking") and not abm_config.get("enable_treasury"):
        recommendations.append(
            "Consider enabling staking or treasury for more realistic token economics."
        )

    # Check pricing model
    pricing_model = abm_config.get("pricing_model", "eoe")
    if pricing_model == "eoe" and not abm_config.get("enable_volume"):
        recommendations.append(
            "EOE pricing model benefits from dynamic volume. Consider enabling volume controller."
        )

    # Check Monte Carlo
    if config.get("monte_carlo", {}).get("enabled", False):
        num_trials = config["monte_carlo"].get("num_trials", 100)
        if num_trials < 50:
            recommendations.append(
                f"Monte Carlo with {num_trials} trials may not provide reliable confidence bands. "
                f"Consider increasing to at least 100 trials."
            )

    # Check agent granularity
    agent_granularity = abm_config.get("agent_granularity", "adaptive")
    if agent_granularity == "full_individual":
        recommendations.append(
            "Full individual agent mode may be slow for large holder counts. "
            "Consider using 'adaptive' granularity for better performance."
        )

    return recommendations


def generate_migration_report(
    original_mode: str,
    warnings: List[str],
    recommendations: List[str]
) -> str:
    """
    Generate human-readable migration report.

    Args:
        original_mode: Original simulation mode
        warnings: Migration warnings
        recommendations: Configuration recommendations

    Returns:
        Formatted migration report string
    """
    report = []
    report.append(f"Configuration Migration Report")
    report.append(f"=" * 70)
    report.append(f"Original Mode: {original_mode}")
    report.append(f"Migrated To: ABM (Agent-Based Model)")
    report.append("")

    if warnings:
        report.append(f"Migration Actions ({len(warnings)}):")
        for i, warning in enumerate(warnings, 1):
            report.append(f"  {i}. {warning}")
        report.append("")

    if recommendations:
        report.append(f"Recommendations ({len(recommendations)}):")
        for i, rec in enumerate(recommendations, 1):
            report.append(f"  {i}. {rec}")
        report.append("")

    report.append(f"=" * 70)
    report.append(f"Migration completed successfully.")

    return "\n".join(report)


# Example usage
if __name__ == "__main__":
    # Test migration of tier2 config
    tier2_config = {
        "token": {
            "name": "TestToken",
            "total_supply": 1_000_000_000,
            "simulation_mode": "tier2"
        },
        "buckets": [
            {"bucket": "Team", "allocation": 30}
        ],
        "tier2": {
            "staking": {
                "enabled": True,
                "apy": 0.15,
                "max_capacity_pct": 0.4
            },
            "pricing": {
                "enabled": True,
                "pricing_model": "bonding_curve"
            },
            "volume": {
                "enabled": True,
                "volume_model": "proportional",
                "base_daily_volume": 20_000_000
            }
        }
    }

    print("Testing Tier 2 to ABM migration:\n")
    migrated, warnings = migrate_legacy_config(tier2_config)
    recommendations = validate_migrated_config(migrated)
    report = generate_migration_report("tier2", warnings, recommendations)
    print(report)

    print("\n" + "=" * 70 + "\n")

    # Test migration of tier3 config
    tier3_config = {
        "token": {
            "name": "TestToken",
            "total_supply": 1_000_000_000,
            "simulation_mode": "tier3"
        },
        "buckets": [
            {"bucket": "Team", "allocation": 30},
            {"bucket": "VC", "allocation": 40}
        ],
        "tier3": {
            "monte_carlo": {
                "enabled": True,
                "num_trials": 200,
                "variance_level": "high"
            },
            "cohort_behavior": {
                "enabled": True,
                "bucket_cohort_mapping": {
                    "Team": "high_stake",
                    "VC": "high_sell"
                }
            }
        }
    }

    print("Testing Tier 3 to ABM migration:\n")
    migrated, warnings = migrate_legacy_config(tier3_config)
    recommendations = validate_migrated_config(migrated)
    report = generate_migration_report("tier3", warnings, recommendations)
    print(report)
