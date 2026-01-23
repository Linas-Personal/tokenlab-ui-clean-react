# Vesting Simulator - User Guide

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Simulation Tiers](#simulation-tiers)
4. [Token Configuration](#token-configuration)
5. [Vesting Buckets](#vesting-buckets)
6. [Behavioral Modifiers](#behavioral-modifiers)
7. [Dynamic Features (Tier 2/3)](#dynamic-features-tier-23)
8. [Understanding the Outputs](#understanding-the-outputs)
9. [Export Options](#export-options)
10. [Common Workflows](#common-workflows)

---

## Overview

The Vesting Simulator is a comprehensive tool for modeling token unlock schedules and market dynamics. It helps project teams:
- Plan token distribution across different stakeholder groups
- Forecast circulating supply over time
- Estimate sell pressure from unlocking tokens
- Model dynamic market behaviors (pricing, staking, treasury)
- Run Monte Carlo simulations for risk analysis

The simulator supports three tiers of complexity, from basic deterministic vesting to advanced stochastic modeling with dynamic market features.

---

## Getting Started

### Launching the Application

```bash
cd tokenlab-abm-ui
python apps/vesting_gradio_app.py
```

The interface will launch at `http://127.0.0.1:7860`

### Quick Start

1. **Configure Token Settings**: Name, ticker, total supply, launch date, simulation horizon
2. **Select Simulation Tier**: Tier 1 (basic), Tier 2 (dynamic), or Tier 3 (Monte Carlo)
3. **Define Vesting Buckets**: Add allocation groups (Team, Investors, Community, etc.)
4. **Enable Behavioral Modifiers** (optional): Cliff shock, price triggers, relocking
5. **Enable Dynamic Features** (Tier 2/3 only): Staking, pricing, treasury, volume
6. **Run Simulation**: Click "Run Simulation" button
7. **Review Results**: Charts, summary cards, and export data

---

## Simulation Tiers

### Tier 1: Basic Vesting
**Use Case**: Straightforward token unlock modeling

**Features**:
- Deterministic vesting schedules
- Basic behavioral modifiers (cliff shock, price triggers, relocking)
- 3 core visualizations
- Fast execution (~1-2 seconds)

**Best For**: Initial planning, simple tokenomics, presentation materials

---

### Tier 2: Dynamic Market Features
**Use Case**: Realistic market dynamics modeling

**Features**:
- All Tier 1 features
- Dynamic staking with APY rewards
- Dynamic pricing (bonding curve or external price scenarios)
- Treasury strategy simulation
- Dynamic volume calculation
- 5 visualizations (adds Price Evolution and Staking Dynamics)
- Medium execution (~2-3 seconds)

**Best For**: Market impact analysis, treasury planning, staking program design

---

### Tier 3: Monte Carlo Simulation
**Use Case**: Risk analysis and probabilistic forecasting

**Features**:
- All Tier 2 features
- Monte Carlo trials with configurable iterations
- Cohort behavior modeling (HODLers, Traders, Opportunists)
- Stochastic outcomes with confidence intervals
- Advanced statistical analysis
- Longer execution time (scales with trial count)

**Best For**: Risk assessment, scenario planning, investor due diligence

---

## Token Configuration

### Token Settings

**Token Name**
- Display name for your project token
- Example: "DeFi Protocol Token"

**Ticker**
- Token symbol (2-6 characters recommended)
- Example: "DPT"

**Total Supply**
- Total number of tokens ever to exist
- Denominated in whole tokens
- Example: 1,000,000,000 (1 billion)
- **Important**: All bucket allocations are percentages of this total supply

**Launch Date**
- Token Generation Event (TGE) date
- Format: YYYY-MM-DD
- Example: "2024-01-01"
- This is "Month 0" for the simulation

**Horizon Months**
- Simulation duration in months
- Recommended: At least as long as your longest vesting schedule + 12 months
- Example: 48 (4 years)
- **Note**: Extending the horizon shows full vesting completion and post-vesting dynamics

---

## Vesting Buckets

Vesting buckets represent different stakeholder groups with distinct unlock schedules.

### Allocation Mode

**Percentage Mode** (Recommended)
- Allocations as % of total supply
- Must sum to ≤100%
- Example: Team 20%, Investors 30%, Community 50%

**Absolute Mode**
- Allocations in absolute token amounts
- Must sum to ≤ total supply
- Example: Team 200M, Investors 300M, Community 500M

### Bucket Parameters

**Bucket Name**
- Identifier for the stakeholder group
- Common examples: Team, Seed, Private, Public, Liquidity, Treasury, Ecosystem

**Allocation**
- % of total supply (percentage mode) OR absolute tokens (absolute mode)
- **Validation**: Total across all buckets cannot exceed 100% / total supply

**TGE Unlock %**
- Percentage of bucket allocation unlocked immediately at launch
- Range: 0-100%
- Example: 10% TGE unlock means 10% available at Month 0
- **Use Case**: Public sale participants often get 10-25% at TGE

**Cliff Months**
- Lockup period before vesting begins
- No tokens unlock during the cliff (except TGE unlock)
- Range: 0-60 months
- Example: 12-month cliff means first vesting after 1 year
- **Use Case**: Team and advisors typically have 6-12 month cliffs

**Vesting Months**
- Duration over which remaining tokens unlock linearly
- Starts AFTER the cliff period
- Range: 0-120 months
- Example: 24-month vesting = linear unlock over 2 years
- **Formula**:
  - Tokens to vest = Allocation × (1 - TGE unlock %)
  - Monthly unlock = Tokens to vest / Vesting months

### Example Bucket Configurations

**Team Bucket**
```
Name: Team
Allocation: 20%
TGE Unlock: 0%
Cliff: 12 months
Vesting: 36 months
```
- Nothing at TGE
- First unlock at Month 12
- Linear unlock over months 12-48

**Public Sale Bucket**
```
Name: Public Sale
Allocation: 10%
TGE Unlock: 25%
Cliff: 0 months
Vesting: 6 months
```
- 25% immediately at TGE
- Remaining 75% unlocks linearly over 6 months

---

## Behavioral Modifiers

Behavioral modifiers add realism by modeling how holders respond to market conditions.

### Cliff Shock

**What It Does**: Models increased selling when large cliffs unlock

**When Cliffs Unlock**: Tokens become liquid after extended lockup periods
**Holder Behavior**: Some holders sell immediately to capture liquidity

**Parameters**:
- **Enable**: Checkbox to activate cliff shock
- **Cliff Shock Multiplier**: Amplification of sell pressure
  - Range: 1.0 - 5.0
  - Example: 2.0 = double the expected sell on cliff unlock months
  - 1.0 = no additional pressure (baseline)
- **Buckets to Apply**: Select which buckets experience cliff shock
  - Typically: Team, Advisors, Early Investors
  - Not typically: Community, Liquidity pools

**Example**:
```
Team bucket has 12-month cliff
200M tokens unlock at Month 12
Cliff shock multiplier: 2.5
Expected sell (no shock): 40M (20% sell pressure)
With cliff shock: 100M (50% sell pressure)
```

---

### Price Triggers

**What It Does**: Models selling behavior based on token price movements

**Price Source**:
- **Scenario**: Use predefined price patterns
  - "stable": Flat price (baseline)
  - "gradual_growth": Slow upward trend
  - "rapid_growth": Fast upward trend
  - "volatile": High volatility with swings
  - "crash_and_recover": Drop then recovery
- **Dynamic Pricing**: Use Tier 2/3 bonding curve pricing

**Parameters**:
- **Take Profit Threshold**: Price multiplier that triggers selling
  - Example: 2.0 = sell when price doubles from initial
  - Range: 1.0 - 10.0
- **Stop Loss Threshold**: Price multiplier that triggers panic selling
  - Example: 0.5 = sell when price drops 50%
  - Range: 0.1 - 1.0
- **Extra Sell %**: Additional selling when triggers activate
  - Example: 30% = sell 30% more than baseline when triggered
  - Range: 0-100%

**Example**:
```
Price starts at $1.00
Take profit: 2.0
Price reaches $2.00 → Holders sell extra 30% of unlocked tokens
```

---

### Relocking

**What It Does**: Models tokens being locked again in staking or governance

**Use Cases**:
- Staking programs
- Governance voting locks
- Liquidity mining incentives

**Parameters**:
- **Relock %**: Percentage of newly unlocked tokens that get relocked
  - Range: 0-100%
  - Example: 40% = 40% of each unlock is immediately relocked
- **Lock Duration**: How long relocked tokens stay locked
  - Range: 1-60 months
  - Example: 12 months = relocked tokens unlock 12 months later

**Example**:
```
Month 6: 100M tokens unlock
Relock: 40%
Lock duration: 12 months

Immediate circulation: 60M
Relocked: 40M (will unlock at Month 18)
```

**Interaction with Staking**: If both relocking and dynamic staking are enabled, relocking represents non-staking locks (e.g., governance).

---

## Dynamic Features (Tier 2/3)

### Dynamic Staking

**What It Does**: Models staking participation and rewards over time

**Parameters**:
- **Enable**: Activate staking dynamics
- **Base APY**: Annual percentage yield for stakers
  - Example: 0.08 = 8% APY
  - Range: 0.01 - 1.00 (1% - 100%)
- **Participation Rate**: % of circulating supply that stakes
  - Example: 0.40 = 40% of circulating tokens are staked
  - Range: 0.05 - 0.95

**How It Works**:
1. Each month, `participation_rate × circulating_supply` tokens are staked
2. Stakers earn `base_apy / 12` monthly rewards
3. Rewards are minted (increase total supply) or from treasury (no supply increase)
4. Staking reduces sell pressure (staked tokens not sold)

**Outputs**:
- Staking Dynamics chart (Tier 2/3)
- Reduced circulating supply available for selling

---

### Dynamic Pricing

**What It Does**: Simulates token price evolution using bonding curve mechanics

**Model**: Bonding Curve
- Price responds to supply/demand dynamics
- Buy pressure increases price
- Sell pressure decreases price

**Parameters**:
- **Enable**: Activate dynamic pricing
- **Initial Price**: Starting price at TGE
  - Example: 1.0 = $1.00
  - Range: Any positive number
- **Elasticity**: Price sensitivity to supply changes
  - Range: 0.1 - 2.0
  - Low (0.1-0.5): Price stable, small reactions
  - Medium (0.5-1.0): Moderate price movements
  - High (1.0-2.0): Volatile, large swings
- **Monthly Buy Pressure**: Constant inflow from buyers
  - Example: 1,000,000 = $1M monthly buy orders
  - Represents organic demand

**Bonding Curve Formula**:
```
Price(t) = Initial_Price × (1 + elasticity × net_flow / circulating_supply)
net_flow = buy_pressure - sell_volume
```

**Outputs**:
- Price Evolution chart (Tier 2/3)
- Dynamic price used for price trigger calculations

**Example**:
```
Initial price: $1.00
Elasticity: 0.5
Month 1:
  - Circulating supply: 10M tokens
  - Sell volume: 2M tokens
  - Buy pressure: 3M tokens
  - Net flow: +1M
  - Price: $1.00 × (1 + 0.5 × 1M/10M) = $1.05
```

---

### Treasury Strategies

**What It Does**: Models how project treasury responds to market conditions

**Distribution** (must sum to 100%):
- **Buyback %**: Treasury buys tokens from market
  - Reduces sell pressure
  - Increases price
- **Liquidity %**: Treasury provides liquidity to DEXs
  - Stabilizes price
  - Enables trading
- **Reserves %**: Treasury holds for future use
  - No immediate market impact
  - Strategic reserve for emergencies

**How It Works**:
1. Treasury receives funds from token sales, fees, or protocol revenue
2. Each month, treasury allocates funds per distribution %
3. Buyback: Acts as buy pressure in pricing model
4. Liquidity: Reduces slippage, stabilizes price
5. Reserves: Accumulates for future deployment

**Example**:
```
Treasury monthly budget: $100,000
Distribution: 30% buyback, 40% liquidity, 30% reserves

Actions:
- $30,000 buyback → Reduces circulating supply
- $40,000 liquidity → Adds to DEX pools
- $30,000 reserves → Held for future
```

---

### Dynamic Volume

**What It Does**: Calculates realistic trading volume based on market conditions

**Factors**:
- Average daily volume input (baseline)
- Price volatility (higher volatility → more volume)
- Unlock events (large unlocks → volume spikes)
- Market trends (bull markets → higher volume)

**Parameter**:
- **Average Daily Volume**: Expected daily trading volume
  - Example: 1,000,000 = $1M/day
  - Used as baseline for volume calculations

**Outputs**:
- Volume affects slippage calculations
- High volume → lower price impact from sells
- Low volume → higher price impact from sells

---

## Understanding the Outputs

### Summary Cards

**Max Monthly Unlock**
- Largest single-month token unlock
- Token amount and month number
- **Use**: Identify peak unlock events

**Max Monthly Sell**
- Largest expected sell volume in one month
- Token amount and month number
- **Use**: Prepare for maximum sell pressure

**Peak Circulating Supply**
- Highest % of total supply in circulation
- Percentage and month number
- **Use**: Understand final circulation level

### Visualizations

**Chart 1: Monthly Unlock Schedule by Bucket**
- **Type**: Stacked bar chart
- **X-axis**: Month (0 = TGE)
- **Y-axis**: Tokens unlocking
- **Colors**: Each bucket has a unique color
- **Interpretation**:
  - Height shows total unlocks per month
  - Color segments show which buckets unlock
  - Identify cliff unlock spikes

**Chart 2: Expected Circulating Supply Over Time**
- **Type**: Dual-axis line chart
- **Left Y-axis**: Absolute tokens (blue line)
- **Right Y-axis**: % of total supply (purple dashed line)
- **X-axis**: Month
- **Interpretation**:
  - Blue area: Total circulating tokens
  - Purple line: Circulation as % of max supply
  - Flattening indicates vesting completion

**Chart 3: Expected Monthly Sell Pressure**
- **Type**: Bar chart
- **X-axis**: Month
- **Y-axis**: Tokens expected to be sold
- **Interpretation**:
  - Height = sell volume
  - Spikes indicate high-risk months
  - Behavioral modifiers affect bar heights

**Chart 4: Price Evolution (Tier 2/3)**
- **Type**: Line chart
- **X-axis**: Month
- **Y-axis**: Token price
- **Interpretation**:
  - Shows simulated price trajectory
  - Drops indicate sell pressure periods
  - Rises indicate buy pressure or low circulation

**Chart 5: Staking Dynamics (Tier 2/3)**
- **Type**: Dual-axis chart (bar + line)
- **Left Y-axis**: Tokens staked (green bars)
- **Right Y-axis**: Participation rate % (red line)
- **X-axis**: Month
- **Interpretation**:
  - Bars: Absolute staked amount
  - Line: % of circulating supply staked
  - Increasing bars = more staking over time

---

## Export Options

### CSV Exports

**Bucket-Level CSV**
- Filename: `{token_ticker}_vesting_by_bucket_{timestamp}.csv`
- Columns: Month, Bucket Name, Unlocked, Locked, Cumulative Unlocked
- **Use**: Detailed bucket-by-bucket analysis, spreadsheet modeling

**Global CSV**
- Filename: `{token_ticker}_vesting_global_{timestamp}.csv`
- Columns: Month, Total Unlocked, Circulating Supply, Expected Sell, Price (if Tier 2/3)
- **Use**: High-level analysis, charting in external tools

### JSON Export

- Filename: `{token_ticker}_config_{timestamp}.json`
- Contains: Full simulation configuration
- **Use**: Save and reload configurations, version control, sharing setups

### PDF Report

- Filename: `{token_ticker}_report_{timestamp}.pdf`
- Contains: All charts in a single document
- **Use**: Presentations, investor materials, documentation

---

## Common Workflows

### Workflow 1: Basic Vesting Plan Review

**Goal**: Validate token unlock schedule

1. Set Tier 1
2. Configure token settings
3. Add vesting buckets (Team, Investors, Community, etc.)
4. Run simulation
5. Check Chart 1 (unlock schedule) for distribution fairness
6. Check Chart 2 (circulating supply) for smooth ramp-up
7. Export PDF for team review

---

### Workflow 2: Sell Pressure Analysis

**Goal**: Identify risky unlock periods

1. Set Tier 1
2. Enable Cliff Shock for Team/Advisors buckets
3. Set realistic cliff shock multiplier (e.g., 2.0)
4. Run simulation
5. Review Chart 3 (sell pressure)
6. Identify months with >$1M expected sell
7. Plan liquidity support for those months

---

### Workflow 3: Staking Program Design

**Goal**: Model staking economics

1. Set Tier 2
2. Enable Dynamic Staking
3. Test different APY values (5%, 10%, 15%)
4. Adjust participation rate (30%, 50%, 70%)
5. Run simulation for each configuration
6. Compare Chart 5 (staking dynamics)
7. Evaluate trade-offs:
   - High APY = more inflation but more staking
   - High participation = less sell pressure
8. Export CSV to calculate total rewards cost

---

### Workflow 4: Price Impact Modeling

**Goal**: Estimate price trajectory under sell pressure

1. Set Tier 2
2. Enable Dynamic Pricing
3. Set initial price (e.g., $1.00)
4. Set elasticity based on market cap:
   - Small cap (<$10M): 1.5 (volatile)
   - Mid cap ($10M-$100M): 0.8 (moderate)
   - Large cap (>$100M): 0.3 (stable)
5. Set monthly buy pressure (expected demand)
6. Run simulation
7. Review Chart 4 (price evolution)
8. Identify months where price drops >20%
9. Plan support (buybacks, marketing, partnerships)

---

### Workflow 5: Monte Carlo Risk Analysis

**Goal**: Understand outcome uncertainty

1. Set Tier 3
2. Configure cohort behaviors
3. Set Monte Carlo trials (100-500)
4. Run simulation (may take 30-60 seconds)
5. Review percentile ranges in outputs
6. Identify worst-case (10th percentile) scenarios
7. Plan risk mitigation for worst-case circulating supply and sell pressure
8. Export data for statistical analysis

---

### Workflow 6: Scenario Comparison

**Goal**: Compare different tokenomics designs

1. Design Scenario A (e.g., long vesting, low TGE)
2. Run simulation, export JSON config
3. Design Scenario B (e.g., short vesting, high TGE)
4. Run simulation, export JSON config
5. Compare CSVs in spreadsheet:
   - Peak circulating supply
   - Total sell pressure
   - Time to 50% circulation
6. Choose optimal scenario

---

### Workflow 7: Edge Case Testing

**Goal**: Validate robustness

See [EDGE_CASES.md](EDGE_CASES.md) for detailed edge case scenarios.

Common edge cases to test:
- All buckets unlock at TGE (0 cliff, 0 vesting)
- Extremely long vesting (120 months)
- Zero TGE unlock with long cliff
- Price crash scenario
- 100% staking participation

---

## Best Practices

### Token Configuration
- Use realistic total supply (typical: 100M - 10B)
- Set horizon ≥ longest vesting + 12 months
- Double-check launch date format (YYYY-MM-DD)

### Vesting Buckets
- Ensure allocations sum to ≤100%
- Use consistent naming (Team, not "Team tokens" vs "TEAM")
- Longer cliffs for insiders (6-12 months)
- Shorter cliffs for community (0-3 months)

### Behavioral Modifiers
- Start with conservative estimates (cliff shock 1.5-2.0)
- Only apply cliff shock to insider buckets
- Use price triggers with realistic thresholds (2x take profit, 0.5x stop loss)
- Relock % should be <50% for most scenarios

### Dynamic Features
- Staking APY: 5-20% is typical for DeFi
- Participation rate: 30-60% is realistic
- Price elasticity: Lower for larger market caps
- Treasury: Balanced distribution (no single category >50%)

### Simulation Workflow
- Start with Tier 1, validate basic schedule
- Add Tier 2 features one at a time
- Use Tier 3 for final validation and risk analysis
- Always export JSON config for reproducibility

---

## Troubleshooting

**Warning: "Total allocation exceeds 100%"**
- Check bucket allocations sum
- Use percentage mode for easier calculation

**Simulation runs but charts look wrong**
- Verify horizon_months is long enough
- Check for negative cliff/vesting values
- Ensure TGE unlock % is 0-100

**Price Evolution shows flat line**
- Increase elasticity (try 0.5-1.0)
- Increase monthly buy pressure
- Check that Dynamic Pricing is enabled

**Staking Dynamics missing**
- Verify Tier 2 or Tier 3 is selected
- Check "Enable Dynamic Staking" is checked

---

## Next Steps

- See [CONFIGURATION.md](CONFIGURATION.md) for detailed parameter reference
- See [EDGE_CASES.md](EDGE_CASES.md) for edge case examples
- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical implementation details
