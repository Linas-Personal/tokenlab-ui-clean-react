# TokenLab ABM UI - Vesting & Allocation Simulator

A comprehensive vesting schedule simulator and sell pressure analyzer built on top of TokenLab's agent-based modeling framework.

## Features

### Tier 1 - Deterministic Analysis
- Cliff + linear vesting schedules
- Configurable sell pressure scenarios
- Cliff shock stress testing
- Price-triggered selling
- Token relock/staking delays

### Tier 2 - Dynamic TokenLab Integration
- Price-supply feedback loops via bonding curves
- Dynamic staking with APY incentives and capacity limits
- Treasury management strategies (hold/liquidity/buyback)
- Volume-liquidity dynamics

### Tier 3 - Advanced Probabilistic Analysis
- Monte Carlo uncertainty analysis with confidence bands
- Cohort-based holder modeling (VCs, team, retail)
- Multi-scenario stress testing

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/tokenlab-abm-ui.git
cd tokenlab-abm-ui

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

## Quick Start

### Using the Gradio UI

```bash
python apps/vesting_gradio_app.py
```

Then open your browser to `http://localhost:7860`

### Using the Python API

```python
from tokenlab_abm.analytics.vesting_simulator import VestingSimulator

# Create configuration
config = {
    "token": {
        "total_supply": 1_000_000_000,
        "start_date": "2026-01-01",
        "horizon_months": 36,
        "allocation_mode": "percent"
    },
    "assumptions": {
        "sell_pressure_level": "medium",
        "avg_daily_volume_tokens": None
    },
    "behaviors": {
        "cliff_shock": {"enabled": False},
        "price_trigger": {"enabled": False},
        "relock": {"enabled": False}
    },
    "buckets": [
        {
            "bucket": "Team",
            "allocation": 20,
            "tge_unlock_pct": 0,
            "cliff_months": 12,
            "vesting_months": 36
        }
    ]
}

# Run Tier 1 simulation
simulator = VestingSimulator(config, mode="tier1")
df_bucket, df_global = simulator.run_simulation()

# Generate charts
figs = simulator.make_charts(df_bucket, df_global)

# Export
simulator.export_csvs("./output")
simulator.export_pdf("./output/report.pdf")
```

#### Using Tier 2/3 Advanced Features

```python
from tokenlab_abm.analytics.vesting_simulator import VestingSimulatorAdvanced

# Add Tier 2/3 configuration
config["tier2"] = {
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
    "treasury": {
        "enabled": True,
        "hold_pct": 0.3,
        "liquidity_pct": 0.5,
        "buyback_pct": 0.2
    },
    "volume": {
        "enabled": True,
        "turnover_rate": 0.01
    }
}

config["tier3"] = {
    "cohorts": {
        "enabled": True,
        "bucket_profiles": {
            "Team": "high_stake",
            "Seed": "high_sell"
        }
    }
}

# Run Tier 2/3 simulation
simulator = VestingSimulatorAdvanced(config, mode="tier3")
df_bucket, df_global = simulator.run_simulation()

# Run Monte Carlo for uncertainty analysis
df_stats, df_all_trials = simulator.run_monte_carlo(num_trials=100)

# Generate enhanced charts (includes price evolution, staking dynamics)
figs = simulator.make_charts()
```

## Documentation

See [docs/vesting_simulator_guide.md](docs/vesting_simulator_guide.md) for comprehensive documentation.

## Architecture

- `src/tokenlab_abm/analytics/vesting_simulator.py` - Core simulation engine
- `apps/vesting_gradio_app.py` - Gradio web interface
- `tests/` - Comprehensive test suite
- `examples/` - Example configurations

## Requirements

- Python >= 3.6
- TokenLab dependencies (numpy, pandas, matplotlib, scipy)
- gradio >= 4.0
- python-dateutil >= 2.8.0

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## Citation

If you use this in research, please cite:

```
@software{tokenlab_vesting_simulator,
  title={TokenLab Vesting \& Allocation Simulator},
  author={TokenLab Contributors},
  year={2026},
  url={https://github.com/YOUR_USERNAME/tokenlab-abm-ui}
}
```
