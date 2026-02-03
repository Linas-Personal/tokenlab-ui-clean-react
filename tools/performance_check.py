import json
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from tokenlab_abm.analytics.vesting_simulator import VestingSimulatorAdvanced, MonteCarloRunner


def run_simulation(config, mode):
    start = time.perf_counter()
    simulator = VestingSimulatorAdvanced(config, mode=mode)
    simulator.run_simulation()
    elapsed = time.perf_counter() - start
    return elapsed


def run_monte_carlo(config, num_trials):
    start = time.perf_counter()
    runner = MonteCarloRunner(config, variance_level=config["tier3"]["monte_carlo"]["variance_level"])
    runner.run(num_trials=num_trials, mode="tier1")
    elapsed = time.perf_counter() - start
    return elapsed


def main():
    base_config = {
        "token": {
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 36,
            "allocation_mode": "percent",
            "simulation_mode": "tier1",
        },
        "assumptions": {"sell_pressure_level": "medium"},
        "behaviors": {
            "cliff_shock": {"enabled": True},
            "price_trigger": {"enabled": False},
            "relock": {"enabled": False},
        },
        "tier2": {
            "staking": {"enabled": True, "apy": 0.15, "capacity": 0.5, "lockup": 6, "include_rewards": True},
            "pricing": {"enabled": True, "model": "bonding_curve", "initial_price": 1.0, "elasticity": 0.5},
            "treasury": {"enabled": True, "hold_pct": 0.3, "liquidity_pct": 0.5, "buyback_pct": 0.2},
            "volume": {"enabled": True, "base_volume": 1_000_000, "volatility": 0.2},
        },
        "tier3": {
            "cohorts": {
                "enabled": True,
                "bucket_profiles": {
                    "Team": "high_stake",
                    "Seed": "high_sell",
                    "Community": "balanced",
                },
            },
            "monte_carlo": {"enabled": True, "num_trials": 30, "variance_level": 0.1},
        },
        "buckets": [
            {"bucket": "Team", "allocation": 40, "tge_unlock_pct": 0, "cliff_months": 12, "vesting_months": 24},
            {"bucket": "Seed", "allocation": 30, "tge_unlock_pct": 10, "cliff_months": 6, "vesting_months": 18},
            {"bucket": "Community", "allocation": 30, "tge_unlock_pct": 5, "cliff_months": 0, "vesting_months": 36},
        ],
    }

    results = {}
    results["tier1"] = run_simulation(base_config, "tier1")
    results["tier2"] = run_simulation(base_config, "tier2")
    results["tier3"] = run_simulation(base_config, "tier3")
    results["monte_carlo_trials_30"] = run_monte_carlo(base_config, 30)

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "config": {
            "horizon_months": base_config["token"]["horizon_months"],
            "buckets": [bucket["bucket"] for bucket in base_config["buckets"]],
            "tier2_features": {"staking": True, "pricing": "bonding_curve", "treasury": True, "volume": True},
            "tier3_features": {"cohorts": True, "monte_carlo_trials": 30},
        },
        "results_seconds": {k: round(v, 4) for k, v in results.items()},
    }

    report_path = PROJECT_ROOT / "PERFORMANCE_VERIFICATION.md"
    report_lines = [
        "# Performance Verification",
        "",
        f"Generated: {report['timestamp']}",
        "",
        "## Environment",
        f"- Python: {report['python_version']}",
        f"- Platform: {report['platform']}",
        "",
        "## Scenario",
        f"- Horizon months: {report['config']['horizon_months']}",
        f"- Buckets: {', '.join(report['config']['buckets'])}",
        f"- Tier 2 features: {json.dumps(report['config']['tier2_features'])}",
        f"- Tier 3 features: {json.dumps(report['config']['tier3_features'])}",
        "",
        "## Results (seconds)",
    ]
    for key, value in report["results_seconds"].items():
        report_lines.append(f"- {key}: {value}")
    report_lines.append("")

    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
