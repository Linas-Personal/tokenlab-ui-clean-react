# TokenLab Vesting Simulator - User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Features](#features)
5. [Configuration](#configuration)
6. [Tier 2: Dynamic TokenLab Integration](#tier-2-dynamic-tokenlab-integration)
7. [Tier 3: Advanced Uncertainty Analysis](#tier-3-advanced-uncertainty-analysis)
8. [Use Cases](#use-cases)
9. [API Reference](#api-reference)

## Introduction

The TokenLab Vesting Simulator is a comprehensive tool for analyzing token vesting schedules and expected sell pressure. It provides deterministic modeling of unlock patterns with configurable behavioral assumptions.

### Key Features
- **Cliff + Linear Vesting**: Standard TGE + cliff + linear vesting schedules
- **Behavioral Modifiers**: Cliff shock, price triggers, relock/staking delays
- **Multiple Buckets**: Team, investors, treasury, liquidity - unlimited categories
- **Rich Visualizations**: 3 professional charts with export capabilities
- **Export Options**: CSV (2 files), PDF report, JSON configuration

## Installation

### Prerequisites
- Python 3.6 or higher
- pip package manager

### Install via pip

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/tokenlab-abm-ui.git
cd tokenlab-abm-ui

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### Verify Installation

```bash
python -c "from tokenlab_abm.analytics.vesting_simulator import VestingSimulator; print('Installation successful!')"
```

## Quick Start

### Using the Gradio Web Interface

1. Launch the application:
```bash
python apps/vesting_gradio_app.py
```

2. Open your browser to `http://localhost:7860`

3. The UI has 4 tabs:
   - **Token Setup**: Define supply, TGE date, and simulation horizon
   - **Vesting Schedule**: Input your vesting table
   - **Assumptions & Behaviors**: Configure sell pressure and modifiers
   - **Results**: View charts, metrics, and download exports

### Using the Python API

```python
from tokenlab_abm.analytics.vesting_simulator import VestingSimulator

# Define configuration
config = {
    "token": {
        "name": "MyToken",
        "total_supply": 1_000_000_000,
        "start_date": "2026-01-01",
        "horizon_months": 36,
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
            "bucket": "Team",
            "allocation": 20,
            "tge_unlock_pct": 0,
            "cliff_months": 12,
            "vesting_months": 36
        }
    ]
}

# Run simulation
simulator = VestingSimulator(config)
df_bucket, df_global = simulator.run_simulation()

# Generate charts
figs = simulator.make_charts()

# Export results
simulator.export_csvs("./output")
simulator.export_pdf("./output/report.pdf")
```

## Features

### 1. Vesting Schedule Configuration

#### Allocation Modes
- **Percent Mode**: Allocations sum to 100%
- **Token Mode**: Allocations specified in absolute token amounts

#### Vesting Parameters Per Bucket
- **Bucket Name**: Identifier (Team, Seed, etc.)
- **Allocation**: Percentage or token amount
- **TGE Unlock %**: Percentage unlocked at TGE (0-100)
- **Cliff Months**: Delay before vesting starts
- **Vesting Months**: Linear vesting duration after cliff

#### Example Vesting Schedules

**Conservative (Long Lock)**
```
Team:      20% | TGE: 0%   | Cliff: 12mo | Vesting: 36mo
Seed:      10% | TGE: 10%  | Cliff: 6mo  | Vesting: 18mo
Treasury:  30% | TGE: 0%   | Cliff: 0mo  | Vesting: 48mo
Liquidity: 40% | TGE: 100% | Cliff: 0mo  | Vesting: 0mo
```

**Aggressive (Short Lock)**
```
Team:      15% | TGE: 5%   | Cliff: 6mo  | Vesting: 12mo
Investors: 25% | TGE: 20%  | Cliff: 3mo  | Vesting: 9mo
Liquidity: 60% | TGE: 100% | Cliff: 0mo  | Vesting: 0mo
```

### 2. Sell Pressure Configuration

Three preset levels based on market research:
- **Low (10%)**: Conservative assumption, strong holder base
- **Medium (25%)**: Moderate assumption, typical for good projects
- **High (50%)**: Aggressive assumption, weak holder base or bear market

### 3. Behavioral Modifiers

#### Cliff Shock
**Purpose**: Stress-test first unlock after cliff
**Parameters**:
- Multiplier (1.0 - 5.0): Sell pressure multiplier for first vest month
- Buckets: Select which allocations are affected

**Use Case**: Early investors often dump at first unlock opportunity

**Example**:
- Base sell pressure: 25%
- Cliff shock multiplier: 3x
- Effective sell pressure at first unlock: 75% (capped at 100%)

#### Price-Triggered Selling
**Purpose**: Model stop-loss / take-profit behavior
**Parameters**:
- Take-Profit Threshold: Price increase % that triggers selling
- Stop-Loss Threshold: Price decrease % that triggers selling
- Extra Sell Add-On: Additional sell pressure when triggered
- Price Source: Flat, Scenario (uptrend/downtrend/volatile), or CSV upload

**Use Case**: Holders react to price movements

**Example**:
- Take-profit at +50% → extra 20% sell pressure
- Stop-loss at -30% → extra 20% sell pressure
- Base 25% + 20% addon = 45% effective sell when triggered

#### Relock / Staking Delay
**Purpose**: Model tokens being relocked or staked
**Parameters**:
- Relock Percentage (0-100%): % of unlocked tokens relocked
- Lock Duration: Months before relocked tokens mature

**Use Case**: Staking incentives delay sell pressure

**Example**:
- 30% of unlocks are relocked for 6 months
- Month 13: Unlock 100M, relock 30M, sell 17.5M (25% of 70M)
- Month 19: Matured 30M available to sell

**Note**: Relock only applies to post-cliff vesting unlocks, not TGE

### 4. Visualizations

#### Chart 1: Unlock Schedule (Stacked Bar)
- **X-Axis**: Month
- **Y-Axis**: Tokens unlocked
- **Colors**: One per bucket
- **Insights**: Identify cliff dates, peak unlock months

#### Chart 2: Circulating Supply (Dual Y-Axis Line)
- **Left Y-Axis**: Absolute circulating tokens
- **Right Y-Axis**: Percentage of total supply
- **Insights**: Track supply inflation over time

#### Chart 3: Expected Sell Pressure (Bar)
- **X-Axis**: Month
- **Y-Axis**: Expected tokens sold
- **Insights**: Identify high-pressure months

### 5. Summary Metrics

- **Max Monthly Unlock**: Largest single-month unlock and when it occurs
- **Max Monthly Sell**: Largest expected sell volume and when it occurs
- **Circulating at Key Milestones**: Month 12, 24, and end

### 6. Export Formats

#### CSV Exports
1. **Bucket Schedule**: Detailed monthly data per bucket
   - Columns: month_index, date, bucket, allocation, unlocked_this_month, unlocked_cumulative, locked_remaining, sell_pressure, expected_sell, expected_circulating_cumulative

2. **Global Metrics**: Aggregated monthly totals
   - Columns: month_index, date, total_unlocked, total_expected_sell, expected_circulating_total, expected_circulating_pct, sell_volume_ratio

#### PDF Report
Single-page summary with:
- Project metadata
- Key metrics
- All 3 charts
- Timestamp and generation info

#### JSON Configuration
Complete configuration export for reproducibility. Can be imported to restore exact simulation state.

## Configuration

### Config Schema

```json
{
  "token": {
    "name": "string",
    "total_supply": "integer",
    "start_date": "YYYY-MM-DD",
    "horizon_months": "integer (12-60)",
    "allocation_mode": "percent | tokens"
  },
  "assumptions": {
    "sell_pressure_level": "low | medium | high",
    "avg_daily_volume_tokens": "float | null"
  },
  "behaviors": {
    "cliff_shock": {
      "enabled": "boolean",
      "multiplier": "float (1.0-5.0)",
      "buckets": ["string", ...]
    },
    "price_trigger": {
      "enabled": "boolean",
      "source": "flat | scenario | csv",
      "scenario": "uptrend | downtrend | volatile",
      "take_profit": "float (0.1-2.0)",
      "stop_loss": "float (-0.9 to -0.1)",
      "extra_sell_addon": "float (0-0.5)",
      "uploaded_price_series": [[month, price], ...]
    },
    "relock": {
      "enabled": "boolean",
      "relock_pct": "float (0-1.0)",
      "lock_duration_months": "integer"
    }
  },
  "buckets": [
    {
      "bucket": "string",
      "allocation": "float",
      "tge_unlock_pct": "float (0-100)",
      "cliff_months": "integer (0+)",
      "vesting_months": "integer (0+)",
      "unlock_type": "linear"
    }
  ]
}
```

### Validation Rules

- Total supply must be positive
- Start date must be YYYY-MM-DD format
- Horizon must be positive
- TGE unlock % must be 0-100
- Cliff and vesting months must be non-negative
- Allocation mode "percent": sum should equal 100% (warns if not)
- Allocation mode "tokens": sum must not exceed total supply

## Tier 2: Dynamic TokenLab Integration

Tier 2 adds dynamic economic modeling using TokenLab components. These features make the simulation more realistic by modeling feedback loops and economic dynamics.

### Dynamic Staking with APY

**Purpose**: Replace simple relock with realistic staking behavior based on incentives.

**Features**:
- **APY-Based Participation**: Higher APY → higher participation rate
- **Capacity Limits**: Max % of circulating supply that can stake
- **Yield Generation**: Optional staking rewards (increases supply)
- **Maturity Tracking**: Automatically tracks when staked tokens unlock

**Configuration**:
```json
"tier2": {
  "staking": {
    "enabled": true,
    "apy": 0.15,
    "capacity": 0.60,
    "lockup": 6,
    "include_rewards": true
  }
}
```

**Example**: With 15% APY and 60% capacity:
- Month 13: 100M unlocks, 60M can stake (capacity limit)
- Participation: ~70% of available capacity stakes
- Month 19: 42M matures (principal + 6-month yield)

### Dynamic Pricing

**Purpose**: Model price response to circulating supply changes.

**Models**:
1. **Constant**: Fixed price (Tier 1 behavior)
2. **Linear**: P = P₀ × (1 - elasticity × (S/S_max))
3. **Bonding Curve**: P = P₀ × (S_max / S)^elasticity

**Configuration**:
```json
"tier2": {
  "pricing": {
    "enabled": true,
    "model": "bonding_curve",
    "initial_price": 1.0,
    "elasticity": 0.5
  }
}
```

**Example**: Bonding curve with elasticity 0.5:
- 10% circulating → price = $3.16
- 50% circulating → price = $1.41
- 100% circulating → price = $1.00

### Treasury Strategies

**Purpose**: Model treasury deployment decisions (hold vs provide liquidity vs buyback).

**Strategies**:
- **Hold**: Keep tokens in treasury (not circulating)
- **Liquidity**: Deploy to DEX (counts as circulating, increases volume)
- **Buyback**: Remove from total supply (deflationary)

**Configuration**:
```json
"tier2": {
  "treasury": {
    "enabled": true,
    "hold_pct": 0.3,
    "liquidity_pct": 0.5,
    "buyback_pct": 0.2
  }
}
```

**Example**: Treasury unlocks 100M per month:
- 30M held (not circulating)
- 50M deployed to liquidity (increases circulating + trading volume)
- 20M bought back (reduces total supply from 1B to 980M)

### Dynamic Volume

**Purpose**: Calculate trading volume based on circulating supply and liquidity.

**Formula**: Volume = circulating × turnover_rate × liquidity_multiplier

**Configuration**:
```json
"tier2": {
  "volume": {
    "enabled": true,
    "turnover_rate": 0.01
  }
}
```

**Example**: With 1% turnover:
- 100M circulating, 10M liquidity → ~316K daily volume
- 500M circulating, 50M liquidity → ~1.58M daily volume

## Tier 3: Advanced Uncertainty Analysis

Tier 3 adds Monte Carlo simulation and cohort-based behavior modeling for uncertainty quantification.

### Monte Carlo Simulation

**Purpose**: Generate uncertainty bands (P10, P50, P90) by running multiple trials with randomized parameters.

**Randomized Parameters**:
- **Cliff Timing**: ±1-2 months
- **TGE Unlock %**: ±5%
- **Vesting Duration**: ±10%
- **Sell Pressure**: ±5%

**Configuration**:
```json
"tier3": {
  "monte_carlo": {
    "enabled": true,
    "num_trials": 100,
    "variance_level": 0.10
  }
}
```

**Usage**:
```python
simulator = VestingSimulatorAdvanced(config, mode="tier3")
df_stats, df_all = simulator.run_monte_carlo(num_trials=100)

# df_stats contains P10, P50, P90 per month
p10_sell = df_stats["total_expected_sell_<lambda>"]  # 10th percentile
p50_sell = df_stats["total_expected_sell_median"]    # Median
p90_sell = df_stats["total_expected_sell_<lambda>.1"] # 90th percentile
```

**Example**: Month 13 expected sell:
- P10: 15.2M (optimistic case)
- P50: 18.7M (median case)
- P90: 22.1M (pessimistic case)

### Cohort-Based Behaviors

**Purpose**: Different allocation buckets have different behavior profiles.

**Behavior Profiles**:

| Profile | Stake % | Sell % | Description |
|---------|---------|--------|-------------|
| `high_stake` | 70% | 30% | Team, long-term holders |
| `high_sell` | 10% | 90% | VCs, short-term holders |
| `balanced` | 40% | 60% | Community |
| `treasury` | 0% | 0% | Treasury (handled separately) |

**Configuration**:
```json
"tier3": {
  "cohorts": {
    "enabled": true,
    "bucket_profiles": {
      "Team": "high_stake",
      "Seed": "high_sell",
      "Private": "high_sell",
      "Community": "balanced"
    }
  }
}
```

**Example**: With base sell pressure 25%:
- Team (high_stake): Effective sell ~8.3% (70% stake, 30% of 25% sell)
- Seed (high_sell): Effective sell ~90% (10% stake, 90% of 25% sell)
- Community (balanced): Effective sell ~60% (40% stake, 60% of 25% sell)

### Combining Tier 2 + Tier 3

You can enable both tiers simultaneously for maximum realism:

```python
config = {
    "token": {...},
    "assumptions": {...},
    "behaviors": {...},
    "tier2": {
        "staking": {"enabled": True, ...},
        "pricing": {"enabled": True, ...},
        "treasury": {"enabled": True, ...},
        "volume": {"enabled": True, ...}
    },
    "tier3": {
        "cohorts": {"enabled": True, ...},
        "monte_carlo": {"enabled": True, ...}
    },
    "buckets": [...]
}

simulator = VestingSimulatorAdvanced(config, mode="tier3")
df_bucket, df_global = simulator.run_simulation()
df_stats, df_all = simulator.run_monte_carlo(num_trials=100)
```

## Use Cases

### 1. Investor Due Diligence
**Scenario**: Evaluating investment in a new project

**Steps**:
1. Input project's vesting schedule
2. Use medium sell pressure as baseline
3. Enable cliff shock for investor buckets
4. Review max unlock months - are they manageable?
5. Check circulating at month 12 - is it reasonable for exchange listings?

**Red Flags**:
- >50% of supply circulating in first 6 months
- Multiple large unlocks in same month
- No cliff for team allocation

### 2. Tokenomics Design
**Scenario**: Designing vesting for your project

**Steps**:
1. Start with template (Team/Seed/Private/Treasury/Liquidity)
2. Adjust cliffs to align with project milestones
3. Run simulation with high sell pressure to stress-test
4. Iterate until circulating supply growth is smooth
5. Export charts for tokenomics deck

**Best Practices**:
- Team cliff >= 12 months
- Seed/Private cliff >= 6 months
- Treasury vests linearly from day 1
- Liquidity 100% at TGE

### 3. Exchange Listing Planning
**Scenario**: Planning liquidity for exchange listing

**Steps**:
1. Input current vesting schedule
2. Note circulating supply at target listing date
3. Enable relock to model staking programs
4. Check if circulating supply meets exchange minimum
5. Adjust TGE unlocks if needed

**Exchange Requirements**:
- Typically need 10-20% circulating minimum
- Higher is better for trading volume
- Balance with sell pressure concerns

### 4. Price Impact Analysis
**Scenario**: Understanding sell pressure timing

**Steps**:
1. Input vesting schedule
2. Enable price trigger with scenarios
3. Run uptrend scenario - when does take-profit trigger?
4. Run downtrend scenario - when does stop-loss trigger?
5. Use results to plan market-making strategies

**Insights**:
- Large unlocks during downtrend → amplified selling
- Small unlocks during uptrend → taking profits early
- Plan liquidity provision accordingly

### 5. Staking Program Design
**Scenario**: Designing staking to reduce sell pressure

**Steps**:
1. Run baseline without relock
2. Note problematic high-sell months
3. Enable relock with various percentages
4. Find minimum relock % that smooths sell pressure
5. Set staking APY to achieve that participation rate

**Tradeoffs**:
- Higher relock % → delayed sell pressure
- Longer lock duration → more smoothing
- But: staking rewards increase supply inflation

## API Reference

### VestingSimulator Class (Tier 1)

```python
class VestingSimulator:
    def __init__(self, config: dict, mode: str = "tier1")
    def run_simulation() -> Tuple[pd.DataFrame, pd.DataFrame]
    def make_charts(df_bucket: pd.DataFrame, df_global: pd.DataFrame) -> List[plt.Figure]
    def export_csvs(output_dir: str) -> Tuple[str, str]
    def export_pdf(output_path: str) -> str
    def to_json() -> str
    @staticmethod
    def from_json(json_str: str) -> VestingSimulator
```

### VestingSimulatorAdvanced Class (Tier 2/3)

```python
class VestingSimulatorAdvanced(VestingSimulator):
    def __init__(self, config: dict, mode: str = "tier1")  # mode: "tier1", "tier2", or "tier3"
    def run_simulation() -> Tuple[pd.DataFrame, pd.DataFrame]
    def make_charts() -> List[plt.Figure]  # Includes extra charts for Tier 2/3
    def run_monte_carlo(num_trials: int = 100) -> Tuple[pd.DataFrame, pd.DataFrame]
    def export_csvs(output_dir: str) -> Tuple[str, str]
    def export_pdf(output_path: str) -> str
```

**Tier 2/3 Component Classes**:

```python
# Tier 2: Staking
class DynamicStakingController:
    def __init__(self, config: dict, vesting_economy: VestingTokenEconomy)
    def calculate_participation_rate(self, month_index: int) -> float
    def apply_staking(self, unlocked_amount: float, month_index: int) -> Tuple[float, float]
    def get_matured_stake(self, month_index: int) -> float

# Tier 2: Pricing
class DynamicPricingController:
    def __init__(self, config: dict, vesting_economy: VestingTokenEconomy)
    def calculate_price(self, circulating_supply: float) -> float

# Tier 2: Treasury
class TreasuryStrategyController:
    def __init__(self, config: dict, vesting_economy: VestingTokenEconomy)
    def add_tokens(self, amount: float)
    def deploy_strategy(self, month_index: int) -> Tuple[float, float, float]

# Tier 2: Volume
class DynamicVolumeCalculator:
    def __init__(self, config: dict)
    def calculate_volume(self, circulating_supply: float, liquidity_deployed: float) -> float

# Tier 3: Monte Carlo
class MonteCarloRunner:
    def __init__(self, base_config: dict, variance_level: float = 0.10)
    def apply_noise(self, config: dict, seed: int) -> dict
    def run(self, num_trials: int = 100, mode: str = "tier2") -> Tuple[pd.DataFrame, pd.DataFrame]

# Tier 3: Cohorts
class CohortBehaviorController:
    def __init__(self, config: dict)
    def get_behavior_multiplier(self, bucket_name: str) -> float
```

### Helper Functions

```python
def validate_config(config: dict) -> List[str]
def normalize_config(config: dict) -> dict
```

### VestingBucketController Class

```python
class VestingBucketController:
    def __init__(self, bucket_config: dict, global_config: dict)
    def execute(month_index: int, current_price: float, initial_price: float) -> float
    def get_history() -> dict
    def reset()
```

### VestingTokenEconomy Class

```python
class VestingTokenEconomy:
    def __init__(self, config: dict)
    def change_supply(self, delta: float)
    def update_price(self, new_price: float)
    def update_circulating(self, new_circulating: float)
    def advance_iteration()
    def reset()
```

## Troubleshooting

### Common Issues

**Issue**: "Allocation sum exceeds 100%"
**Solution**: In percent mode, allocations must sum to ≤100%

**Issue**: "start_date must be in YYYY-MM-DD format"
**Solution**: Use ISO format, e.g., "2026-01-01"

**Issue**: Charts not displaying
**Solution**: Ensure matplotlib backend is configured correctly

**Issue**: PDF export fails
**Solution**: Check write permissions in output directory

**Issue**: Gradio UI won't launch
**Solution**: Check port 7860 is not in use: `netstat -an | findstr 7860`

### Getting Help

- GitHub Issues: https://github.com/YOUR_USERNAME/tokenlab-abm-ui/issues
- Documentation: This file
- Examples: See `examples/` directory

## Changelog

### v0.2.0 (2026-01-23)
- **Tier 2: Dynamic TokenLab Integration**
  - Dynamic staking with APY incentives and capacity limits
  - Dynamic pricing with bonding curves and linear demand models
  - Treasury strategies (hold/liquidity/buyback)
  - Dynamic volume calculation based on circulating supply
- **Tier 3: Advanced Uncertainty Analysis**
  - Monte Carlo simulation with parameter noise (P10/P50/P90 bands)
  - Cohort-based behavior modeling (different profiles per bucket)
- **UI Enhancements**
  - Added "Advanced (Tier 2/3)" configuration tab in Gradio UI
  - Simulation mode selector (Tier1/Tier2/Tier3)
  - Additional charts for price evolution and staking dynamics
- **Testing**
  - Expanded test suite to 29 tests (17 Tier 1 + 12 Tier 2/3)
  - 100% test pass rate
- **Documentation**
  - Comprehensive Tier 2/3 feature documentation
  - Updated API reference for VestingSimulatorAdvanced

### v0.1.0 (2026-01-23)
- Initial release
- Tier 1 deterministic vesting simulator
- Gradio web interface
- 3 behavioral modifiers (cliff shock, price triggers, relock)
- CSV, PDF, JSON exports
- Comprehensive test suite (17 tests)

## License

MIT License - see LICENSE file for details

## Citation

```bibtex
@software{tokenlab_vesting_simulator,
  title={TokenLab Vesting \& Allocation Simulator},
  author={TokenLab Contributors},
  year={2026},
  url={https://github.com/YOUR_USERNAME/tokenlab-abm-ui}
}
```
