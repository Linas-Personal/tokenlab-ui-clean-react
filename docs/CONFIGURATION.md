# Vesting Simulator - Configuration Reference

## Table of Contents
1. [Configuration Structure](#configuration-structure)
2. [Token Settings](#token-settings)
3. [Simulation Settings](#simulation-settings)
4. [Vesting Buckets](#vesting-buckets)
5. [Behavioral Modifiers](#behavioral-modifiers)
6. [Dynamic Features](#dynamic-features)
7. [Monte Carlo Settings](#monte-carlo-settings)
8. [Complete Example](#complete-example)

---

## Configuration Structure

The simulator accepts a JSON configuration with the following top-level keys:

```json
{
  "token": { /* Token settings */ },
  "simulation": { /* Simulation parameters */ },
  "buckets": [ /* Vesting buckets */ ],
  "behaviors": { /* Behavioral modifiers */ },
  "dynamic_staking": { /* Staking configuration */ },
  "dynamic_pricing": { /* Pricing model */ },
  "treasury_strategies": { /* Treasury management */ },
  "dynamic_volume": { /* Volume modeling */ },
  "monte_carlo": { /* Monte Carlo settings (Tier 3) */ }
}
```

---

## Token Settings

### `token` (required)

Top-level configuration for token metadata.

```json
{
  "token": {
    "name": string,
    "ticker": string,
    "total_supply": number,
    "launch_date": string
  }
}
```

#### Parameters

**`name`** (string, required)
- Token display name
- **Example**: `"My DeFi Token"`
- **Validation**: None (free text)
- **Default**: "Token"

**`ticker`** (string, required)
- Token symbol/ticker
- **Example**: `"MDT"`
- **Validation**: None (free text)
- **Recommendation**: 2-6 uppercase characters
- **Default**: "TKN"

**`total_supply`** (number, required)
- Total token supply (max tokens ever)
- **Example**: `1000000000` (1 billion)
- **Unit**: Whole tokens (not wei/decimals)
- **Validation**: Must be positive
- **Warning**: If ≤ 0, warns "total_supply should be positive"
- **Default**: 1,000,000

**`launch_date`** (string, required)
- Token Generation Event (TGE) date
- **Format**: `"YYYY-MM-DD"` (ISO 8601)
- **Example**: `"2024-06-15"`
- **Validation**: Must match YYYY-MM-DD format
- **Warning**: If invalid format, warns and uses default
- **Default**: `"2024-01-01"`

---

## Simulation Settings

### `simulation` (required)

Simulation runtime parameters.

```json
{
  "simulation": {
    "horizon_months": number,
    "allocation_mode": string
  }
}
```

#### Parameters

**`horizon_months`** (number, required)
- Simulation duration in months
- **Example**: `48` (4 years)
- **Range**: 1 - 240 (typical: 24-60)
- **Validation**: Must be positive integer
- **Recommendation**: Set to `max(cliff + vesting) + 12` to see full vesting completion
- **Default**: 36

**`allocation_mode`** (string, optional)
- How bucket allocations are specified
- **Options**:
  - `"percentage"`: Allocations as % of total_supply (0-100)
  - `"absolute"`: Allocations in absolute token amounts
- **Example**: `"percentage"`
- **Default**: `"percentage"`

---

## Vesting Buckets

### `buckets` (required)

Array of vesting bucket configurations. Each bucket represents a stakeholder group.

```json
{
  "buckets": [
    {
      "name": string,
      "allocation_pct": number,      // If allocation_mode = "percentage"
      "allocation_absolute": number,  // If allocation_mode = "absolute"
      "tge_unlock_pct": number,
      "cliff_months": number,
      "vesting_months": number,
      "cliff_shock_pct": number
    }
  ]
}
```

#### Parameters

**`name`** (string, required)
- Bucket identifier
- **Example**: `"Team"`, `"Seed Investors"`, `"Community"`
- **Validation**: None (free text)
- **Recommendation**: Use consistent naming conventions

**`allocation_pct`** (number, required if `allocation_mode="percentage"`)
- Percentage of total_supply allocated to this bucket
- **Example**: `20` (20% of total supply)
- **Range**: 0 - 100
- **Validation**: Sum of all buckets must ≤ 100
- **Error**: If sum > 100, critical error raised
- **Warning**: If sum < 100, warning shown (unallocated supply)

**`allocation_absolute`** (number, required if `allocation_mode="absolute"`)
- Absolute number of tokens allocated
- **Example**: `200000000` (200M tokens)
- **Range**: 0 - total_supply
- **Validation**: Sum of all buckets must ≤ total_supply

**`tge_unlock_pct`** (number, required)
- Percentage of bucket allocation unlocked at TGE (Month 0)
- **Example**: `10` (10% unlocked immediately)
- **Range**: 0 - 100
- **Validation**: Clamped to 0-100 range
- **Warning**: If < 0 or > 100, normalized and warned
- **Default**: 0

**`cliff_months`** (number, required)
- Lockup period before vesting starts (months)
- **Example**: `12` (1-year cliff)
- **Range**: 0 - 60 (typical: 0-24)
- **Validation**: Must be non-negative
- **Normalization**: If negative, set to 0
- **Warning**: If < 0, warns "cliff_months should be non-negative"
- **Default**: 0

**`vesting_months`** (number, required)
- Linear vesting duration after cliff (months)
- **Example**: `24` (2-year vesting)
- **Range**: 0 - 120 (typical: 12-48)
- **Validation**: Must be non-negative
- **Normalization**: If negative, set to 0
- **Default**: 0
- **Note**: Total unlock period = cliff_months + vesting_months

**`cliff_shock_pct`** (number, optional)
- Per-bucket cliff shock percentage (overrides global setting)
- **Example**: `50` (50% cliff shock for this bucket)
- **Range**: 0 - 100
- **Default**: Uses global `behaviors.cliff_shock.cliff_shock_pct` if not specified
- **Use**: Override cliff shock for specific buckets

---

## Behavioral Modifiers

### `behaviors` (optional)

Behavioral modifiers model realistic holder actions.

```json
{
  "behaviors": {
    "cliff_shock": { /* Cliff unlock selling */ },
    "price_trigger": { /* Price-based selling */ },
    "relock": { /* Token relocking */ }
  }
}
```

---

### `behaviors.cliff_shock`

Models increased selling when cliff unlocks occur.

```json
{
  "behaviors": {
    "cliff_shock": {
      "enabled": boolean,
      "cliff_shock_pct": number,
      "cliff_shock_buckets": [string]
    }
  }
}
```

#### Parameters

**`enabled`** (boolean, required)
- Activate cliff shock behavior
- **Example**: `true`
- **Default**: `false`

**`cliff_shock_pct`** (number, required if enabled)
- Sell pressure multiplier on cliff unlock months
- **Example**: `50` (50% additional selling = 1.5x multiplier)
- **Range**: 0 - 100 (typical: 10-100)
- **Formula**: `sell_multiplier = 1 + (cliff_shock_pct / 100)`
- **Default**: 0

**`cliff_shock_buckets`** (array of strings, required if enabled)
- List of bucket names to apply cliff shock
- **Example**: `["Team", "Advisors"]`
- **Validation**: Bucket names must exist in `buckets[]`
- **Default**: `[]` (no buckets)

---

### `behaviors.price_trigger`

Models price-based selling behavior (take profit / stop loss).

```json
{
  "behaviors": {
    "price_trigger": {
      "enabled": boolean,
      "price_source": string,
      "take_profit": number,
      "stop_loss": number,
      "extra_sell_pct": number
    }
  }
}
```

#### Parameters

**`enabled`** (boolean, required)
- Activate price trigger behavior
- **Example**: `true`
- **Default**: `false`

**`price_source`** (string, required if enabled)
- Source for price data
- **Options**:
  - `"stable"`: Flat price (no change)
  - `"gradual_growth"`: Slow upward trend
  - `"rapid_growth"`: Fast upward trend
  - `"volatile"`: High volatility
  - `"crash_and_recover"`: Drop then recovery
  - `"dynamic"`: Use Tier 2/3 bonding curve pricing
- **Example**: `"volatile"`
- **Default**: `"stable"`

**`take_profit`** (number, required if enabled)
- Price multiplier triggering profit-taking
- **Example**: `2.0` (sell when price 2x initial)
- **Range**: 1.0 - 10.0 (typical: 1.5-3.0)
- **Formula**: `trigger_price = initial_price × take_profit`
- **Default**: 2.0

**`stop_loss`** (number, required if enabled)
- Price multiplier triggering panic selling
- **Example**: `0.5` (sell when price drops 50%)
- **Range**: 0.1 - 1.0 (typical: 0.5-0.8)
- **Formula**: `trigger_price = initial_price × stop_loss`
- **Default**: 0.5

**`extra_sell_pct`** (number, required if enabled)
- Additional sell % when trigger activates
- **Example**: `30` (30% extra selling)
- **Range**: 0 - 100 (typical: 20-50)
- **Formula**: `sell_amount = base_sell × (1 + extra_sell_pct / 100)`
- **Default**: 0

---

### `behaviors.relock`

Models tokens being relocked in staking/governance.

```json
{
  "behaviors": {
    "relock": {
      "enabled": boolean,
      "relock_pct": number,
      "lock_duration_months": number
    }
  }
}
```

#### Parameters

**`enabled`** (boolean, required)
- Activate relocking behavior
- **Example**: `true`
- **Default**: `false`

**`relock_pct`** (number, required if enabled)
- Percentage of newly unlocked tokens that get relocked
- **Example**: `40` (40% relocked)
- **Range**: 0 - 100 (typical: 20-60)
- **Default**: 0

**`lock_duration_months`** (number, required if enabled)
- How long relocked tokens stay locked
- **Example**: `12` (relocked for 1 year)
- **Range**: 1 - 60 (typical: 6-24)
- **Default**: 12

---

## Dynamic Features

### `dynamic_staking` (Tier 2/3 only)

Models staking program with APY rewards.

```json
{
  "dynamic_staking": {
    "enabled": boolean,
    "base_apy": number,
    "participation_rate": number
  }
}
```

#### Parameters

**`enabled`** (boolean, required)
- Activate staking dynamics
- **Example**: `true`
- **Default**: `false`
- **Note**: Requires Tier 2 or Tier 3 mode

**`base_apy`** (number, required if enabled)
- Annual percentage yield for stakers
- **Example**: `0.08` (8% APY)
- **Range**: 0.01 - 1.00 (1% - 100%)
- **Typical**: 0.05 - 0.20 (5% - 20%)
- **Formula**: `monthly_reward = staked_amount × (base_apy / 12)`
- **Default**: 0.10

**`participation_rate`** (number, required if enabled)
- Percentage of circulating supply that stakes
- **Example**: `0.40` (40% participation)
- **Range**: 0.05 - 0.95 (5% - 95%)
- **Typical**: 0.30 - 0.60 (30% - 60%)
- **Default**: 0.50

---

### `dynamic_pricing` (Tier 2/3 only)

Models token price using bonding curve.

```json
{
  "dynamic_pricing": {
    "enabled": boolean,
    "model": string,
    "initial_price": number,
    "elasticity": number,
    "monthly_buy_pressure": number
  }
}
```

#### Parameters

**`enabled`** (boolean, required)
- Activate dynamic pricing
- **Example**: `true`
- **Default**: `false`
- **Note**: Requires Tier 2 or Tier 3 mode

**`model`** (string, required if enabled)
- Pricing model type
- **Options**:
  - `"bonding_curve"`: Supply/demand-based pricing
- **Example**: `"bonding_curve"`
- **Default**: `"bonding_curve"`

**`initial_price`** (number, required if enabled)
- Token price at TGE
- **Example**: `1.0` ($1.00)
- **Range**: Any positive number
- **Validation**: Must be > 0
- **Default**: 1.0

**`elasticity`** (number, required if enabled)
- Price sensitivity to supply changes
- **Example**: `0.5` (moderate sensitivity)
- **Range**: 0.1 - 2.0
- **Guidelines**:
  - 0.1 - 0.3: Low (large cap, stable)
  - 0.5 - 1.0: Medium (mid cap, typical)
  - 1.0 - 2.0: High (small cap, volatile)
- **Formula**: `price_change = elasticity × (net_flow / circulating_supply)`
- **Default**: 0.5

**`monthly_buy_pressure`** (number, required if enabled)
- Constant monthly buy volume (USD or tokens)
- **Example**: `1000000` ($1M/month buy pressure)
- **Range**: 0 - ∞ (typical: 100K - 10M)
- **Default**: 0

---

### `treasury_strategies` (Tier 2/3 only)

Models treasury management strategies.

```json
{
  "treasury_strategies": {
    "enabled": boolean,
    "distribution": {
      "buyback": number,
      "liquidity": number,
      "reserves": number
    }
  }
}
```

#### Parameters

**`enabled`** (boolean, required)
- Activate treasury strategies
- **Example**: `true`
- **Default**: `false`

**`distribution.buyback`** (number, required if enabled)
- Percentage of treasury used for token buyback
- **Example**: `30` (30% for buyback)
- **Range**: 0 - 100
- **Validation**: buyback + liquidity + reserves must = 100
- **Default**: 0

**`distribution.liquidity`** (number, required if enabled)
- Percentage of treasury used for liquidity provision
- **Example**: `40` (40% for liquidity)
- **Range**: 0 - 100
- **Default**: 0

**`distribution.reserves`** (number, required if enabled)
- Percentage of treasury held in reserves
- **Example**: `30` (30% reserves)
- **Range**: 0 - 100
- **Default**: 0

---

### `dynamic_volume` (Tier 2/3 only)

Models trading volume dynamics.

```json
{
  "dynamic_volume": {
    "enabled": boolean,
    "avg_daily_volume": number
  }
}
```

#### Parameters

**`enabled`** (boolean, required)
- Activate dynamic volume calculation
- **Example**: `true`
- **Default**: `false`

**`avg_daily_volume`** (number, required if enabled)
- Expected average daily trading volume
- **Example**: `1000000` ($1M/day)
- **Range**: 0 - ∞
- **Default**: 0

---

## Monte Carlo Settings

### `monte_carlo` (Tier 3 only)

Monte Carlo simulation parameters.

```json
{
  "monte_carlo": {
    "num_trials": number,
    "cohort_behaviors": {
      "hodler_pct": number,
      "trader_pct": number,
      "opportunist_pct": number
    }
  }
}
```

#### Parameters

**`num_trials`** (number, optional)
- Number of Monte Carlo simulation trials
- **Example**: `100`
- **Range**: 10 - 1000 (typical: 100-500)
- **Note**: Higher values = more accuracy but slower
- **Default**: 100

**`cohort_behaviors.hodler_pct`** (number, optional)
- Percentage of holders who never sell
- **Example**: `0.30` (30% are HODLers)
- **Range**: 0.0 - 1.0
- **Validation**: hodler + trader + opportunist should = 1.0
- **Default**: 0.33

**`cohort_behaviors.trader_pct`** (number, optional)
- Percentage of holders who actively trade
- **Example**: `0.40` (40% are traders)
- **Range**: 0.0 - 1.0
- **Default**: 0.33

**`cohort_behaviors.opportunist_pct`** (number, optional)
- Percentage of holders who sell on specific triggers
- **Example**: `0.30` (30% are opportunists)
- **Range**: 0.0 - 1.0
- **Default**: 0.34

---

## Complete Example

### Example: DeFi Protocol Token

```json
{
  "token": {
    "name": "DeFi Protocol Token",
    "ticker": "DPT",
    "total_supply": 1000000000,
    "launch_date": "2024-06-01"
  },
  "simulation": {
    "horizon_months": 60,
    "allocation_mode": "percentage"
  },
  "buckets": [
    {
      "name": "Team",
      "allocation_pct": 20,
      "tge_unlock_pct": 0,
      "cliff_months": 12,
      "vesting_months": 36,
      "cliff_shock_pct": 30
    },
    {
      "name": "Seed",
      "allocation_pct": 10,
      "tge_unlock_pct": 10,
      "cliff_months": 6,
      "vesting_months": 18,
      "cliff_shock_pct": 50
    },
    {
      "name": "Public",
      "allocation_pct": 15,
      "tge_unlock_pct": 25,
      "cliff_months": 0,
      "vesting_months": 6,
      "cliff_shock_pct": 0
    },
    {
      "name": "Liquidity",
      "allocation_pct": 20,
      "tge_unlock_pct": 100,
      "cliff_months": 0,
      "vesting_months": 0,
      "cliff_shock_pct": 0
    },
    {
      "name": "Ecosystem",
      "allocation_pct": 35,
      "tge_unlock_pct": 5,
      "cliff_months": 0,
      "vesting_months": 48,
      "cliff_shock_pct": 0
    }
  ],
  "behaviors": {
    "cliff_shock": {
      "enabled": true,
      "cliff_shock_pct": 40,
      "cliff_shock_buckets": ["Team", "Seed"]
    },
    "price_trigger": {
      "enabled": true,
      "price_source": "dynamic",
      "take_profit": 2.0,
      "stop_loss": 0.5,
      "extra_sell_pct": 30
    },
    "relock": {
      "enabled": true,
      "relock_pct": 40,
      "lock_duration_months": 12
    }
  },
  "dynamic_staking": {
    "enabled": true,
    "base_apy": 0.12,
    "participation_rate": 0.50
  },
  "dynamic_pricing": {
    "enabled": true,
    "model": "bonding_curve",
    "initial_price": 1.0,
    "elasticity": 0.6,
    "monthly_buy_pressure": 500000
  },
  "treasury_strategies": {
    "enabled": true,
    "distribution": {
      "buyback": 30,
      "liquidity": 50,
      "reserves": 20
    }
  },
  "dynamic_volume": {
    "enabled": true,
    "avg_daily_volume": 1000000
  },
  "monte_carlo": {
    "num_trials": 200,
    "cohort_behaviors": {
      "hodler_pct": 0.35,
      "trader_pct": 0.40,
      "opportunist_pct": 0.25
    }
  }
}
```

**Interpretation**:
- 5 buckets (Team, Seed, Public, Liquidity, Ecosystem)
- Total allocation: 100%
- Team: 12-month cliff, 36-month vesting, 30% cliff shock
- Staking: 12% APY, 50% participation
- Pricing: Bonding curve, $1 initial, 0.6 elasticity
- Treasury: 30% buyback, 50% liquidity, 20% reserves
- Monte Carlo: 200 trials, 35% HODLers

---

## Configuration Tips

1. **Start Simple**: Use Tier 1 with minimal behaviors first
2. **Validate Allocations**: Always check sum = 100%
3. **Test Edge Cases**: Try extreme values to understand boundaries
4. **Export Configs**: Save JSON for reproducibility
5. **Version Control**: Track config changes in git

---

## Next Steps

- See [USER_GUIDE.md](USER_GUIDE.md) for workflow examples
- See [EDGE_CASES.md](EDGE_CASES.md) for boundary testing
- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
