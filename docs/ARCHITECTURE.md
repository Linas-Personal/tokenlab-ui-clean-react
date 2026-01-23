# Vesting Simulator - Architecture & Simulation Principles

## Table of Contents
1. [Overview](#overview)
2. [Simulation Principles](#simulation-principles)
3. [Core Architecture](#core-architecture)
4. [Tier 1: Deterministic Engine](#tier-1-deterministic-engine)
5. [Tier 2: Dynamic Market Simulation](#tier-2-dynamic-market-simulation)
6. [Tier 3: Monte Carlo & Stochastic Modeling](#tier-3-monte-carlo--stochastic-modeling)
7. [Data Flow](#data-flow)
8. [Key Algorithms](#key-algorithms)
9. [Performance Considerations](#performance-considerations)
10. [Extension Points](#extension-points)

---

## Overview

The Vesting Simulator is built on **agent-based modeling (ABM)** principles, where individual stakeholder groups ("buckets") act as agents with distinct behaviors and unlock schedules. The simulation progresses month-by-month, calculating token flows, market dynamics, and holder behaviors at each time step.

### Core Principles

1. **Time-stepped simulation**: Discrete monthly intervals from Month 0 (TGE) to horizon
2. **Agent-based modeling**: Each vesting bucket is an autonomous agent with:
   - State (locked tokens, unlocked tokens, cliff status)
   - Behavior (selling rules, relocking, staking)
   - Interactions (market price, treasury, staking pool)
3. **Emergent dynamics**: System-level outcomes (price, circulating supply) emerge from agent interactions
4. **Deterministic → Stochastic progression**: Tier 1 (deterministic) → Tier 2 (dynamic feedback) → Tier 3 (stochastic)

---

## Simulation Principles

### Principle 1: Token State Machine

Each bucket's tokens exist in one of several states:

```
[Total Allocation]
    ↓
[TGE Unlock] → [Immediately Circulating]
    ↓
[Locked (Cliff)] → (Time passes) → [Locked (Vesting)]
    ↓
[Monthly Unlock] → [Circulating] → [Behavioral Filter]
                                        ↓
                    ┌───────────────────┼───────────────────┐
                    ↓                   ↓                   ↓
              [Sold (Sell Pressure)]  [Relocked]  [Staked (Tier 2/3)]
```

**State Transitions** (per month):
1. Calculate vesting schedule unlock
2. Apply behavioral modifiers (cliff shock, price triggers)
3. Route tokens to sell, relock, or stake
4. Update circulating supply and market state

---

### Principle 2: Behavioral Layering

Behaviors are applied as **filters** to unlocked tokens:

```python
unlocked_tokens = calculate_vesting_unlock(month)

# Layer 1: Cliff shock
if is_cliff_month:
    sell_multiplier = 1 + (cliff_shock_pct / 100)
    unlocked_tokens *= sell_multiplier

# Layer 2: Price triggers
if price_triggered(current_price):
    extra_sell = unlocked_tokens * (extra_sell_pct / 100)
    unlocked_tokens += extra_sell

# Layer 3: Relocking
relocked = unlocked_tokens * (relock_pct / 100)
available_to_sell = unlocked_tokens - relocked

# Layer 4: Staking (Tier 2/3)
staked = available_to_sell * staking_participation_rate
final_sell = available_to_sell - staked
```

This **layered approach** allows complex interactions while maintaining clarity.

---

### Principle 3: Supply-Demand Equilibrium (Tier 2)

Tier 2 introduces **feedback loops** between supply and price:

```
[Unlock Events] → [Sell Pressure] → [Supply Increase]
                                          ↓
                                    [Price Decrease]
                                          ↓
                                    [Buy Pressure]
                                          ↓
[Staking Demand] ← [Reduced Sell] ← [Price Increase]
```

**Bonding Curve Pricing**:
```python
price(t) = initial_price × (1 + elasticity × (net_flow / circulating_supply))
net_flow = buy_pressure - sell_volume
```

Price and supply **co-evolve** each time step.

---

### Principle 4: Stochastic Sampling (Tier 3)

Tier 3 uses **Monte Carlo** to model uncertainty:

```
Input Distribution:
- Cliff shock: Normal(μ=50%, σ=20%)
- Participation rate: Beta(α=5, β=3)
- Price elasticity: Uniform(0.3, 0.8)

Monte Carlo Process:
FOR trial = 1 to N:
    1. Sample parameters from distributions
    2. Run deterministic simulation with sampled values
    3. Record outcomes (circulating supply, sell pressure, price)

Aggregate Results:
- Percentiles (10th, 50th, 90th)
- Mean and standard deviation
- Confidence intervals
```

**Cohort Behaviors**: Holders are split into groups with different strategies:
- **HODLers**: Never sell (0% sell rate)
- **Traders**: Sell based on price movements (high sensitivity)
- **Opportunists**: Sell on specific triggers (cliff unlocks, 2x price)

Each trial samples from these cohorts to create variance.

---

## Core Architecture

### Class Hierarchy

```
VestingSimulator (Tier 1)
    ├── __init__(config, mode)
    ├── run_simulation()           # Main simulation loop
    ├── _calculate_monthly_unlock() # Vesting math
    ├── _apply_behaviors()          # Cliff shock, triggers, relock
    ├── make_charts()               # 3 base charts
    └── export_csvs(), export_pdf(), export_json()

VestingSimulatorAdvanced (Tier 2/3) extends VestingSimulator
    ├── __init__(config, mode)
    ├── run_simulation()           # Overrides with dynamic features
    ├── _update_staking()          # Staking controller
    ├── _update_pricing()          # Pricing controller
    ├── _update_treasury()         # Treasury controller
    ├── _make_price_chart()        # Chart 4
    ├── _make_staking_chart()      # Chart 5
    └── run_monte_carlo()          # Tier 3 only
```

### Controller Pattern (Tier 2/3)

Dynamic features are encapsulated in **controllers**:

```
DynamicStakingController
    - Manages staking pool state
    - Calculates APY rewards
    - Tracks participation rates

DynamicPricingController
    - Implements bonding curve
    - Calculates price each month
    - Handles buy/sell pressure

TreasuryStrategyController
    - Allocates treasury funds
    - Executes buybacks
    - Manages liquidity provision

DynamicVolumeCalculator
    - Estimates trading volume
    - Adjusts for volatility
    - Calculates slippage
```

**Why Controllers?**
- Separation of concerns
- Easy to add new features (e.g., new pricing models)
- Testable in isolation

---

## Tier 1: Deterministic Engine

### Algorithm: Monthly Unlock Calculation

```python
def calculate_monthly_unlock(bucket, month):
    """
    Calculate tokens unlocking for a bucket in a given month.

    Vesting schedule:
    - Month 0: TGE unlock (immediate)
    - Months 1 to cliff_months: Zero unlock (cliff)
    - Month cliff_months: First vesting unlock
    - Months cliff_months+1 to cliff_months+vesting_months: Linear vesting
    """

    allocation = bucket.allocation_pct * total_supply / 100

    # TGE unlock (Month 0 only)
    if month == 0:
        return allocation * (bucket.tge_unlock_pct / 100)

    # Cliff period (no unlock)
    if month <= bucket.cliff_months:
        return 0

    # Vesting period
    if month <= bucket.cliff_months + bucket.vesting_months:
        # Tokens remaining to vest
        remaining = allocation * (1 - bucket.tge_unlock_pct / 100)

        # Monthly vesting amount
        monthly_unlock = remaining / bucket.vesting_months

        return monthly_unlock

    # After vesting complete
    return 0
```

**Key Insight**: Vesting is **linear** and **deterministic** given config.

---

### Algorithm: Cliff Shock Application

```python
def apply_cliff_shock(bucket, month, unlocked_tokens):
    """
    Apply cliff shock multiplier if this month is a cliff unlock.
    """

    # Check if this is the first unlock after cliff
    is_cliff_month = (month == bucket.cliff_months + 1) and (bucket.cliff_months > 0)

    if not is_cliff_month:
        return unlocked_tokens

    # Check if bucket is in cliff shock list
    if bucket.name not in config.cliff_shock_buckets:
        return unlocked_tokens

    # Apply multiplier
    multiplier = 1 + (config.cliff_shock_pct / 100)
    shocked_unlock = unlocked_tokens * multiplier

    return shocked_unlock
```

**Rationale**: Cliff unlocks represent **first liquidity** after long lockups, triggering higher selling.

---

## Tier 2: Dynamic Market Simulation

### Algorithm: Bonding Curve Pricing

```python
class DynamicPricingController:
    def __init__(self, config):
        self.initial_price = config.initial_price
        self.elasticity = config.elasticity
        self.monthly_buy_pressure = config.monthly_buy_pressure
        self.current_price = self.initial_price

    def update_price(self, sell_volume, circulating_supply):
        """
        Update price based on bonding curve model.

        Formula:
        Δprice = elasticity × (net_flow / circulating_supply) × current_price

        Where:
        - net_flow = buy_pressure - sell_volume
        - Positive net_flow → price increases
        - Negative net_flow → price decreases
        """

        net_flow = self.monthly_buy_pressure - sell_volume

        # Avoid division by zero
        if circulating_supply == 0:
            return self.current_price

        # Calculate price change
        price_change_pct = self.elasticity * (net_flow / circulating_supply)

        # Update price
        new_price = self.current_price * (1 + price_change_pct)

        # Clamp to avoid negative prices
        new_price = max(new_price, 0.01)

        self.current_price = new_price
        return new_price
```

**Economic Model**: Price adjusts based on **relative supply/demand** balance.

**Elasticity Interpretation**:
- Low (0.1-0.3): Large cap, deep liquidity (small price impact)
- Medium (0.5-0.8): Mid cap, typical DeFi (moderate price impact)
- High (1.0-2.0): Small cap, thin liquidity (high price impact)

---

### Algorithm: Dynamic Staking

```python
class DynamicStakingController:
    def __init__(self, config):
        self.base_apy = config.base_apy
        self.participation_rate = config.participation_rate
        self.staked_amounts = []

    def update_staking(self, month, circulating_supply):
        """
        Update staking pool each month.

        Process:
        1. Calculate target staked amount (participation × circulating)
        2. Calculate APY rewards (monthly)
        3. Add rewards to total supply
        4. Update staked amount
        """

        # Target staked amount
        target_staked = circulating_supply * self.participation_rate

        # Monthly APY (annualized / 12)
        monthly_apy = self.base_apy / 12

        # Calculate rewards on existing stake
        if month > 0:
            rewards = self.staked_amounts[month - 1] * monthly_apy
        else:
            rewards = 0

        # New staked amount = target + rewards
        new_staked = target_staked + rewards

        self.staked_amounts.append(new_staked)

        # Return rewards (increases total supply)
        return rewards
```

**Key Mechanics**:
- Staking **reduces sell pressure** (staked tokens not sold)
- Rewards **increase total supply** (inflation)
- Participation rate is **exogenous** (could be endogenous in future)

---

## Tier 3: Monte Carlo & Stochastic Modeling

### Algorithm: Monte Carlo Loop

```python
def run_monte_carlo(self, num_trials=100):
    """
    Run Monte Carlo simulation with stochastic parameters.

    Returns:
    - df_stats: Percentiles (10th, 50th, 90th) for key metrics
    - df_all_trials: Full results for all trials
    """

    results = []

    for trial in range(num_trials):
        # Sample stochastic parameters
        sampled_config = self._sample_parameters(self.config)

        # Run deterministic simulation with sampled config
        simulator = VestingSimulatorAdvanced(sampled_config, mode="tier2")
        df_bucket, df_global = simulator.run_simulation()

        # Store results
        results.append(df_global)

    # Aggregate results
    df_all_trials = pd.concat(results, keys=range(num_trials))

    # Calculate statistics
    df_stats = df_all_trials.groupby('month_index').agg({
        'expected_circulating_total': ['mean', 'std', lambda x: x.quantile(0.1), lambda x: x.quantile(0.9)],
        'total_expected_sell': ['mean', 'std', lambda x: x.quantile(0.1), lambda x: x.quantile(0.9)]
    })

    return df_stats, df_all_trials
```

---

### Algorithm: Cohort Behavior Sampling

```python
def _sample_cohort_behavior(self, bucket, cohort_config):
    """
    Sample holder cohort for a bucket.

    Cohorts:
    - HODLers: 0% sell rate
    - Traders: High sell rate, price-sensitive
    - Opportunists: Medium sell rate, trigger-sensitive
    """

    # Sample cohort proportions
    hodler_pct = cohort_config.get('hodler_pct', 0.33)
    trader_pct = cohort_config.get('trader_pct', 0.33)
    opportunist_pct = cohort_config.get('opportunist_pct', 0.34)

    # Random assignment
    cohort = np.random.choice(
        ['hodler', 'trader', 'opportunist'],
        p=[hodler_pct, trader_pct, opportunist_pct]
    )

    # Set sell rate based on cohort
    if cohort == 'hodler':
        sell_rate = 0.0
    elif cohort == 'trader':
        sell_rate = np.random.uniform(0.4, 0.8)
    else:  # opportunist
        sell_rate = np.random.uniform(0.2, 0.5)

    return cohort, sell_rate
```

**Variance Sources**:
1. Parameter sampling (cliff shock, APY, elasticity)
2. Cohort assignment (HODLer vs Trader vs Opportunist)
3. Stochastic events (price shocks, volume spikes)

---

## Data Flow

### Monthly Simulation Step

```
START MONTH m
    ↓
[1. Calculate Vesting Unlocks]
    - For each bucket: calculate monthly unlock
    - Sum to get total monthly unlock
    ↓
[2. Apply Behavioral Modifiers]
    - Cliff shock (if cliff month)
    - Price triggers (if enabled)
    - Relocking (if enabled)
    ↓
[3. Update Market State (Tier 2/3)]
    - Staking: Calculate staked amount, mint rewards
    - Pricing: Update price based on sell pressure
    - Treasury: Allocate funds (buyback, liquidity, reserves)
    - Volume: Calculate trading volume
    ↓
[4. Calculate Sell Pressure]
    - Expected sell = unlocked - relocked - staked
    ↓
[5. Update Circulating Supply]
    - Add monthly unlock
    - Subtract relocked
    - Add staking rewards (if Tier 2/3)
    ↓
[6. Record State]
    - Store: unlock, circulating, sell, price, staked
    ↓
END MONTH m → START MONTH m+1
```

### Data Structures

**DataFrame: df_bucket** (bucket-level granularity)
```
Columns:
- month_index: 0, 1, 2, ...
- bucket_name: "Team", "Seed", etc.
- unlocked_this_month: Tokens unlocking this month
- cumulative_unlocked: Total unlocked to date
- locked_remaining: Tokens still locked
```

**DataFrame: df_global** (system-level aggregates)
```
Columns:
- month_index: 0, 1, 2, ...
- total_monthly_unlock: Sum across all buckets
- expected_circulating_total: Total circulating supply
- expected_circulating_pct: % of total supply
- total_expected_sell: Expected sell pressure
- price: Token price (Tier 2/3 only)
- staked_amount: Total staked (Tier 2/3 only)
```

---

## Key Algorithms

### Algorithm: Normalization Pipeline

**Problem**: User inputs may be invalid (negative cliff, TGE > 100%, etc.)

**Solution**: Two-stage validation + normalization

```python
def validate_config(config):
    """
    Stage 1: Validate and return warnings.
    Does not modify config.
    """
    warnings = []

    if config['token']['total_supply'] <= 0:
        warnings.append("total_supply should be positive")

    for bucket in config['buckets']:
        if bucket['tge_unlock_pct'] < 0 or bucket['tge_unlock_pct'] > 100:
            warnings.append(f"TGE unlock for {bucket['name']} should be 0-100")

    return warnings

def normalize_config(config):
    """
    Stage 2: Fix invalid values.
    Returns corrected config.
    """
    normalized = copy.deepcopy(config)

    # Clamp TGE unlock to 0-100 range
    for bucket in normalized['buckets']:
        bucket['tge_unlock_pct'] = max(0, min(100, bucket['tge_unlock_pct']))
        bucket['cliff_months'] = max(0, bucket['cliff_months'])
        bucket['vesting_months'] = max(0, bucket['vesting_months'])

    return normalized
```

**Usage in UI**:
```python
# Validate (show warnings)
warnings = validate_config(config)
display_warnings(warnings)

# Normalize (fix issues)
config = normalize_config(config)

# Run simulation with normalized config
simulator.run_simulation()
```

---

### Algorithm: Export to PDF

```python
def export_pdf(self, output_path):
    """
    Export all charts to a single PDF report.

    Uses matplotlib's PdfPages for multi-page PDF.
    """
    from matplotlib.backends.backend_pdf import PdfPages

    figs = self.make_charts()

    with PdfPages(output_path) as pdf:
        for fig in figs:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)  # Free memory

    return output_path
```

**Memory Management**: Close figures after saving to prevent memory leaks.

---

## Performance Considerations

### Time Complexity

**Tier 1**:
- O(M × B) where M = horizon_months, B = number of buckets
- Typical: 48 months × 5 buckets = 240 operations
- **Execution**: ~1-2 seconds

**Tier 2**:
- O(M × B) + O(M × F) where F = number of dynamic features
- Additional overhead from controllers (staking, pricing, treasury)
- **Execution**: ~2-3 seconds

**Tier 3**:
- O(N × M × B) where N = num_trials
- Scales linearly with trial count
- Typical: 100 trials × 48 months × 5 buckets = 24,000 operations
- **Execution**: ~10-30 seconds for 100 trials

### Memory Complexity

- **df_bucket**: O(M × B) rows
- **df_global**: O(M) rows
- **Charts**: O(M) points per chart (5 charts max)

For typical params (M=48, B=5):
- df_bucket: 240 rows × 8 columns ≈ 15 KB
- df_global: 48 rows × 12 columns ≈ 4 KB
- **Total memory**: < 1 MB per simulation

**Tier 3 Monte Carlo**:
- N trials × (15 KB + 4 KB) ≈ 1.9 MB for 100 trials
- Still very manageable

### Optimization Strategies

1. **Vectorization**: Use numpy/pandas operations instead of loops
2. **Lazy evaluation**: Only calculate charts when requested
3. **Caching**: Cache intermediate results (e.g., vesting schedule)
4. **Parallel Monte Carlo**: Could parallelize trials (not implemented)

---

## Extension Points

### Adding New Pricing Models

Currently supports bonding curve. To add AMM model:

```python
class AMMPricingController(DynamicPricingController):
    def __init__(self, config):
        super().__init__(config)
        self.liquidity_pool_x = config.initial_liquidity_x
        self.liquidity_pool_y = config.initial_liquidity_y

    def update_price(self, sell_volume, circulating_supply):
        """
        Constant product AMM: x × y = k
        """
        k = self.liquidity_pool_x * self.liquidity_pool_y

        # Sell increases x pool
        new_x = self.liquidity_pool_x + sell_volume

        # Constant product
        new_y = k / new_x

        # Price = y / x
        new_price = new_y / new_x

        self.liquidity_pool_x = new_x
        self.liquidity_pool_y = new_y
        self.current_price = new_price

        return new_price
```

Register in config:
```python
if config['dynamic_pricing']['model'] == 'amm':
    self.pricing_controller = AMMPricingController(config)
```

---

### Adding New Behavioral Modifiers

To add "Panic Sell" behavior:

```python
def apply_panic_sell(bucket, month, unlocked_tokens, price_history):
    """
    Apply panic selling if price drops >30% in 7 days.
    """
    if len(price_history) < 2:
        return unlocked_tokens

    price_change = (price_history[-1] - price_history[-2]) / price_history[-2]

    if price_change < -0.30:
        panic_multiplier = 2.0  # Double selling
        return unlocked_tokens * panic_multiplier

    return unlocked_tokens
```

Add to behavior pipeline:
```python
unlocked = apply_cliff_shock(...)
unlocked = apply_price_triggers(...)
unlocked = apply_panic_sell(...)  # NEW
unlocked = apply_relocking(...)
```

---

### Adding New Cohort Types

Currently: HODLer, Trader, Opportunist

To add "Whale" cohort:

```python
def _sample_cohort_behavior(self, bucket, cohort_config):
    cohorts = ['hodler', 'trader', 'opportunist', 'whale']
    probs = [0.3, 0.3, 0.3, 0.1]

    cohort = np.random.choice(cohorts, p=probs)

    if cohort == 'whale':
        # Whales sell large amounts at specific times
        sell_rate = 1.0 if month in whale_sell_months else 0.0
    elif cohort == 'hodler':
        sell_rate = 0.0
    # ... etc

    return cohort, sell_rate
```

---

## Technical Stack

### Dependencies

- **numpy**: Numerical operations, array math
- **pandas**: DataFrame operations, time series
- **matplotlib**: Chart generation
- **scipy**: Statistical functions (Tier 3)
- **statsmodels**: Time series analysis (optional)
- **gradio**: Web UI framework

### Design Patterns

1. **Strategy Pattern**: Controllers (staking, pricing, treasury)
2. **Template Method**: `run_simulation()` in base class, overridden in subclass
3. **Factory Pattern**: Chart creation (`make_charts()`)
4. **Decorator Pattern**: Behavioral modifiers layered on unlock calculations

---

## Next Steps for Developers

To understand the codebase:

1. **Read**: `src/tokenlab_abm/analytics/vesting_simulator.py` (1800 lines)
   - Start with `VestingSimulator.__init__()` and `run_simulation()`
   - Trace through one monthly step
2. **Run**: `pytest tests/test_vesting_simulator.py -v`
   - See actual inputs/outputs
3. **Experiment**: Modify parameters in Gradio UI
   - See how changes propagate
4. **Extend**: Add a new behavioral modifier or pricing model
   - Follow extension patterns above

---

## References

- **Agent-Based Modeling**: Bonabeau, E. (2002). "Agent-based modeling: Methods and techniques for simulating human systems"
- **Monte Carlo Simulation**: Kroese, D.P., et al. (2014). "Why the Monte Carlo method is so important today"
- **Tokenomics**: Crypto economic design patterns (various whitepapers)
- **Bonding Curves**: Bancor Protocol whitepaper (2017)

---

## Summary

The Vesting Simulator uses:
- **Agent-based modeling** for stakeholder groups
- **Time-stepped simulation** for month-by-month progression
- **Layered behaviors** for complex interactions
- **Feedback loops** for dynamic market effects (Tier 2)
- **Monte Carlo sampling** for uncertainty (Tier 3)

Core algorithm: Calculate unlocks → Apply behaviors → Update market → Record state → Repeat

All built on standard Python data science stack (numpy, pandas, matplotlib) with clean abstractions for extensibility.
