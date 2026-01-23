# Vesting Simulator - TokenLab ABM UI

A comprehensive token vesting schedule simulator for modeling unlock schedules, sell pressure, and market dynamics. Supports three tiers of complexity from basic deterministic vesting to advanced Monte Carlo simulations with dynamic pricing and staking.

## Overview

The Vesting Simulator helps crypto projects:
- **Plan token distribution** across stakeholder groups (Team, Investors, Community, etc.)
- **Forecast circulating supply** and unlock schedules over time
- **Estimate sell pressure** from vesting events with behavioral modeling
- **Model market dynamics** including pricing, staking, and treasury strategies
- **Analyze risk** with Monte Carlo simulations and cohort behaviors

Perfect for tokenomics design, investor due diligence, and treasury planning.

## Features by Tier

### Tier 1: Basic Vesting (Fast & Simple)
✓ Deterministic vesting schedules (TGE unlock, cliff, linear vesting)
✓ Behavioral modifiers (cliff shock, price triggers, relocking)
✓ 3 core visualizations (unlock schedule, circulating supply, sell pressure)
✓ Export to CSV, PDF, JSON
✓ ~1-2 second execution

**Use Case**: Initial planning, presentations, basic tokenomics

### Tier 2: Dynamic Market Features (Realistic)
✓ All Tier 1 features
✓ Dynamic staking with APY rewards
✓ Bonding curve pricing with supply/demand feedback
✓ Treasury strategies (buyback, liquidity, reserves)
✓ Dynamic volume calculation
✓ 5 visualizations (adds Price Evolution, Staking Dynamics)
✓ ~2-3 second execution

**Use Case**: Market impact analysis, staking program design, treasury planning

### Tier 3: Monte Carlo Simulation (Risk Analysis)
✓ All Tier 2 features
✓ Monte Carlo trials with configurable iterations
✓ Cohort behavior modeling (HODLers, Traders, Opportunists)
✓ Stochastic outcomes with confidence intervals
✓ Advanced statistical analysis

**Use Case**: Risk assessment, scenario planning, investor presentations

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/linstan1/tokenlab-abm-ui.git
cd tokenlab-abm-ui

# Install dependencies
pip install -r requirements.txt
```

### Launch the Web Interface

```bash
python apps/vesting_gradio_app.py
```

Open your browser to `http://127.0.0.1:7860`

### Basic Workflow

1. **Configure Token**: Set name, ticker, total supply, launch date
2. **Select Tier**: Choose Tier 1 (basic), 2 (dynamic), or 3 (Monte Carlo)
3. **Add Vesting Buckets**: Define stakeholder groups with unlock schedules
4. **Enable Features**: Add cliff shock, price triggers, staking, etc.
5. **Run Simulation**: Click "Run Simulation"
6. **Review Results**: Analyze charts, summary cards, and export data

## Documentation

Comprehensive guides and reference materials:

- **[User Guide](docs/USER_GUIDE.md)** - Complete tutorial on using all features, workflows, and interpreting outputs
- **[Configuration Reference](docs/CONFIGURATION.md)** - Detailed parameter documentation for every configuration option
- **[Edge Cases & Examples](docs/EDGE_CASES.md)** - Edge case scenarios, boundary conditions, and real-world examples
- **[Architecture & Principles](docs/ARCHITECTURE.md)** - How the simulator works, simulation principles, and technical implementation

### Key Concepts

**Vesting Buckets**: Stakeholder groups (Team, Seed, Public, etc.) with distinct unlock schedules
- **TGE Unlock**: % unlocked immediately at launch
- **Cliff**: Lockup period before vesting starts
- **Vesting**: Linear unlock duration after cliff

**Behavioral Modifiers**: Realistic holder responses
- **Cliff Shock**: Increased selling when large cliffs unlock
- **Price Triggers**: Take profit / stop loss selling based on price movements
- **Relocking**: Tokens locked again in staking/governance

**Dynamic Features (Tier 2/3)**:
- **Staking**: APY rewards, participation rates, reduced sell pressure
- **Pricing**: Bonding curve model with supply/demand feedback
- **Treasury**: Buyback, liquidity provision, reserves management
- **Volume**: Dynamic trading volume calculations

**Monte Carlo (Tier 3)**: Stochastic simulation with cohort behaviors (HODLers, Traders, Opportunists)

## Example Output

The simulator generates:
- **Summary Cards**: Max monthly unlock, max sell pressure, peak circulating supply
- **Chart 1**: Monthly unlock schedule by bucket (stacked bar chart)
- **Chart 2**: Circulating supply over time (dual-axis line chart)
- **Chart 3**: Expected monthly sell pressure (bar chart)
- **Chart 4** (Tier 2/3): Price evolution (line chart)
- **Chart 5** (Tier 2/3): Staking dynamics (dual-axis chart)
- **Exports**: CSV (bucket-level and global), PDF report, JSON configuration

## Repository Structure

```
tokenlab-abm-ui/
├── src/tokenlab_abm/analytics/
│   └── vesting_simulator.py      # Core simulation engine (Tier 1, 2, 3)
├── apps/
│   └── vesting_gradio_app.py     # Gradio web interface
├── docs/
│   ├── USER_GUIDE.md             # Complete user guide
│   ├── CONFIGURATION.md          # Parameter reference
│   ├── EDGE_CASES.md             # Edge cases & examples
│   └── ARCHITECTURE.md           # Technical architecture
├── tests/
│   ├── test_vesting_simulator.py # Core tests (50 tests)
│   ├── test_edge_cases.py        # Edge case tests
│   ├── test_ui_integration.py    # UI integration tests
│   └── conftest.py               # Pytest configuration
└── requirements.txt              # Pinned dependencies
```

## Testing

All features are tested with integration tests (no mocks):

```bash
# Run full test suite (50 tests)
pytest tests/ -v

# Run specific test file
pytest tests/test_edge_cases.py -v

# Run with coverage
pytest tests/ --cov=src/tokenlab_abm --cov-report=html
```

Test coverage includes:
- Basic vesting schedules (TGE, cliff, vesting)
- Behavioral modifiers (cliff shock, price triggers, relocking)
- Dynamic features (staking, pricing, treasury, volume)
- Monte Carlo simulations
- Edge cases (zero supply, extreme values, invalid inputs)
- UI integration workflows

## Requirements

- **Python**: 3.13+ (tested on 3.13.4)
- **Dependencies**: See `requirements.txt` (all versions pinned)
  - matplotlib==3.10.3
  - numpy==2.2.6
  - pandas==2.3.0
  - gradio==6.4.0
  - pytest==9.0.2

## Deployment Checklist

Before deploying to production:
- ✅ All 50 tests pass with real execution (no mocks)
- ✅ Error handling with proper logging
- ✅ No hardcoded secrets
- ✅ Performance acceptable (Tier1: 1.7s, Tier2: 2.3s, Tier3: 2.2s)
- ✅ Dependencies pinned with exact versions
- ✅ Git rollback path configured
- ✅ Monitoring via Gradio built-in logging

## Contributing

Contributions welcome! Areas for improvement:
- Additional pricing models (AMM, order book)
- More cohort behavior profiles
- Enhanced visualizations
- Performance optimizations for Tier 3

## License

MIT License

## Citation

If you use this in research or production:

```bibtex
@software{tokenlab_vesting_simulator_2026,
  title={Vesting Simulator - TokenLab ABM UI},
  author={TokenLab Contributors},
  year={2026},
  url={https://github.com/linstan1/tokenlab-abm-ui}
}
```

## Support

- **Issues**: [GitHub Issues](https://github.com/linstan1/tokenlab-abm-ui/issues)
- **Documentation**: See `docs/` folder
- **Tests**: See `tests/` folder for examples
