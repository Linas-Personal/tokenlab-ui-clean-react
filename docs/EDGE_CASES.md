# Vesting Simulator - Edge Cases and Examples

## Table of Contents
1. [Overview](#overview)
2. [Token Configuration Edge Cases](#token-configuration-edge-cases)
3. [Vesting Schedule Edge Cases](#vesting-schedule-edge-cases)
4. [Behavioral Edge Cases](#behavioral-edge-cases)
5. [Pricing Edge Cases](#pricing-edge-cases)
6. [Staking Edge Cases](#staking-edge-cases)
7. [Combined Edge Cases](#combined-edge-cases)
8. [Validation and Normalization](#validation-and-normalization)

---

## Overview

This document covers edge cases, boundary conditions, and special scenarios that the Vesting Simulator handles. Understanding these cases helps you:
- Test the limits of your tokenomics design
- Validate simulator behavior
- Handle unusual but possible real-world situations

All edge cases are **automatically normalized** by the simulator to prevent crashes. Invalid inputs trigger warnings but allow simulation to proceed with corrected values.

---

## Token Configuration Edge Cases

### Edge Case 1: Zero Total Supply

**Configuration**:
```json
{
  "token": {
    "total_supply": 0
  }
}
```

**Behavior**:
- **Warning**: "total_supply should be positive"
- **Normalization**: Simulation may fail or produce zero results
- **Recommendation**: Always use positive total supply (minimum 1,000 tokens)

---

### Edge Case 2: Extremely Large Total Supply

**Configuration**:
```json
{
  "token": {
    "total_supply": 1000000000000000
  }
}
```

**Behavior**:
- Simulation proceeds normally
- Charts may show scientific notation (1e15)
- CSV exports contain full precision
- **Note**: Python handles arbitrary precision integers

**Use Case**: Meme coins or high-supply projects

---

### Edge Case 3: Horizon Shorter Than Vesting

**Configuration**:
```json
{
  "simulation": {
    "horizon_months": 12
  },
  "buckets": [
    {
      "cliff_months": 12,
      "vesting_months": 36
    }
  ]
}
```

**Behavior**:
- Simulation runs for 12 months only
- Charts show partial vesting (truncated)
- Final circulating supply < 100% of total supply
- **Warning**: No explicit warning, but incomplete picture

**Recommendation**: Set `horizon_months ≥ max(cliff_months) + max(vesting_months) + 12`

---

### Edge Case 4: Invalid Date Format

**Configuration**:
```json
{
  "token": {
    "launch_date": "01/01/2024"
  }
}
```

**Behavior**:
- **Warning**: "launch_date must be in YYYY-MM-DD format"
- **Normalization**: Uses default "2024-01-01"

**Valid Format**: "YYYY-MM-DD" (ISO 8601)

---

## Vesting Schedule Edge Cases

### Edge Case 5: Instant 100% Unlock (All TGE)

**Configuration**:
```json
{
  "buckets": [
    {
      "name": "Public",
      "allocation_pct": 100,
      "tge_unlock_pct": 100,
      "cliff_months": 0,
      "vesting_months": 0
    }
  ]
}
```

**Behavior**:
- All tokens unlock at Month 0
- Circulating supply immediately = 100%
- Unlock schedule chart: Single bar at Month 0
- Circulating supply chart: Flat line at 100%

**Use Case**: Launchpad with no vesting, community airdrops

**Risk**: Maximum sell pressure at launch

---

### Edge Case 6: No TGE Unlock + Long Cliff

**Configuration**:
```json
{
  "buckets": [
    {
      "name": "Team",
      "allocation_pct": 100,
      "tge_unlock_pct": 0,
      "cliff_months": 24,
      "vesting_months": 0
    }
  ]
}
```

**Behavior**:
- Zero circulation for 24 months
- All tokens unlock at Month 24 (cliff end)
- Massive spike in Month 24
- Circulating supply: 0% → 100% in one month

**Use Case**: Extreme team lockup

**Risk**: Cliff shock will be severe

---

### Edge Case 7: TGE Unlock > 100%

**Configuration**:
```json
{
  "buckets": [
    {
      "tge_unlock_pct": 150
    }
  ]
}
```

**Behavior**:
- **Warning**: "TGE unlock should be between 0 and 100"
- **Normalization**: Clamped to 100%
- Simulation proceeds with 100% TGE unlock

---

### Edge Case 8: Negative Cliff Months

**Configuration**:
```json
{
  "buckets": [
    {
      "cliff_months": -6
    }
  ]
}
```

**Behavior**:
- **Warning**: "cliff_months should be non-negative"
- **Normalization**: Set to 0 (no cliff)

---

### Edge Case 9: Allocation Exceeds 100%

**Configuration**:
```json
{
  "buckets": [
    {"allocation_pct": 60},
    {"allocation_pct": 50}
  ]
}
```

**Behavior**:
- **Warning**: "Total allocation (110.00%) exceeds 100%"
- **Critical Error**: Simulation fails

**Fix**: Reduce allocations to sum ≤ 100%

---

### Edge Case 10: Empty Buckets List

**Configuration**:
```json
{
  "buckets": []
}
```

**Behavior**:
- **Warning**: "No vesting buckets defined"
- Simulation produces zero unlocks
- All charts show flat zero lines

**Use Case**: Testing infrastructure without tokenomics

---

### Edge Case 11: Extremely Long Vesting (120 months)

**Configuration**:
```json
{
  "buckets": [
    {
      "cliff_months": 12,
      "vesting_months": 120
    }
  ]
}
```

**Behavior**:
- Very slow linear unlock (< 1% per month)
- Requires horizon_months ≥ 132
- Circulating supply chart: Very gradual slope

**Use Case**: Ultra-conservative team vesting

---

## Behavioral Edge Cases

### Edge Case 12: 100% Cliff Shock

**Configuration**:
```json
{
  "behaviors": {
    "cliff_shock": {
      "enabled": true,
      "cliff_shock_pct": 100,
      "cliff_shock_buckets": ["Team"]
    }
  }
}
```

**Behavior**:
- On cliff unlock: All unlocked tokens are sold immediately
- Circulating supply spikes then drops (tokens sold but counted)
- Maximum sell pressure at cliff months

**Use Case**: Worst-case scenario planning

---

### Edge Case 13: Price Stays Exactly the Same

**Configuration**:
```json
{
  "dynamic_pricing": {
    "enabled": true,
    "initial_price": 1.0,
    "elasticity": 0.0
  },
  "behaviors": {
    "price_trigger": {
      "price_source": "stable"
    }
  }
}
```

**Behavior**:
- Price remains flat at initial price
- Zero price triggers activate (no 2x or 0.5x crossings)
- Price Evolution chart: Horizontal line
- Sell pressure unaffected by price

**Use Case**:
- Stablecoin modeling
- Testing sell pressure without price feedback
- Isolating vesting schedule effects

**Notes**:
- Elasticity = 0.0 means price is perfectly inelastic (no supply/demand impact)
- "stable" price scenario maintains constant price
- Useful for baseline comparisons

---

### Edge Case 14: Extreme Price Volatility

**Configuration**:
```json
{
  "behaviors": {
    "price_trigger": {
      "price_source": "volatile",
      "take_profit": 1.1,
      "stop_loss": 0.9,
      "extra_sell_pct": 50
    }
  }
}
```

**Behavior**:
- Price triggers activate frequently
- Sell pressure amplified by 50% during trigger months
- High variance in outcomes

**Use Case**: Meme coin or high-volatility token

---

### Edge Case 15: 100% Relocking

**Configuration**:
```json
{
  "behaviors": {
    "relock": {
      "enabled": true,
      "relock_pct": 100,
      "lock_duration_months": 12
    }
  }
}
```

**Behavior**:
- All unlocked tokens are immediately relocked
- Circulating supply remains near zero
- Tokens continuously cycle through locking
- Sell pressure near zero

**Use Case**: Permanent staking/governance locks

**Note**: Unrealistic for most projects but tests extreme lock behavior

---

### Edge Case 16: Zero Sell Pressure

**Configuration**:
```json
{
  "buckets": [
    {
      "allocation_pct": 100,
      "tge_unlock_pct": 0,
      "cliff_months": 0,
      "vesting_months": 60
    }
  ],
  "behaviors": {
    "relock": {
      "enabled": true,
      "relock_pct": 100,
      "lock_duration_months": 6
    }
  }
}
```

**Behavior**:
- Tokens unlock but are immediately relocked
- Expected sell = 0 for all months
- Circulating supply chart shows accumulation despite zero selling

**Use Case**: Pure governance token with no market trading

---

## Pricing Edge Cases

### Edge Case 17: Zero Monthly Buy Pressure

**Configuration**:
```json
{
  "dynamic_pricing": {
    "enabled": true,
    "initial_price": 1.0,
    "elasticity": 0.5,
    "monthly_buy_pressure": 0
  }
}
```

**Behavior**:
- Only sell pressure affects price (no buyers)
- Price declines continuously
- Price Evolution chart: Downward trend
- May approach zero if sustained selling

**Use Case**: Bear market scenario, failed project

---

### Edge Case 18: Extreme Elasticity

**Configuration**:
```json
{
  "dynamic_pricing": {
    "elasticity": 5.0
  }
}
```

**Behavior**:
- Price extremely sensitive to supply changes
- Large price swings from small unlocks
- Price Evolution chart: High volatility

**Use Case**: Illiquid micro-cap token

**Warning**: Elasticity > 2.0 may produce unrealistic results

---

### Edge Case 19: Initial Price = 0

**Configuration**:
```json
{
  "dynamic_pricing": {
    "initial_price": 0.0
  }
}
```

**Behavior**:
- **Warning**: "Initial price should be positive"
- **Normalization**: Set to default (e.g., 1.0)

---

### Edge Case 20: Bonding Curve with Massive Buy Pressure

**Configuration**:
```json
{
  "dynamic_pricing": {
    "enabled": true,
    "monthly_buy_pressure": 100000000,
    "elasticity": 1.0
  }
}
```

**Behavior**:
- Buy pressure >> sell pressure
- Price increases exponentially
- Price Evolution chart: Steep upward curve
- May trigger take-profit selling

**Use Case**: Viral adoption scenario

---

## Staking Edge Cases

### Edge Case 21: 100% Staking Participation

**Configuration**:
```json
{
  "dynamic_staking": {
    "enabled": true,
    "base_apy": 0.10,
    "participation_rate": 1.0
  }
}
```

**Behavior**:
- All circulating tokens are staked
- Zero tokens available for selling
- Sell pressure = 0
- Staking rewards increase total supply significantly

**Use Case**: Maximum staking adoption

**Note**: Unrealistic (100% participation is impossible in practice)

---

### Edge Case 22: Zero Staking Participation

**Configuration**:
```json
{
  "dynamic_staking": {
    "enabled": true,
    "participation_rate": 0.0
  }
}
```

**Behavior**:
- No tokens staked
- Staking Dynamics chart shows zero bars
- Sell pressure unaffected by staking
- No staking rewards minted

**Use Case**: Failed staking program

---

### Edge Case 23: Extreme APY (500%)

**Configuration**:
```json
{
  "dynamic_staking": {
    "enabled": true,
    "base_apy": 5.0
  }
}
```

**Behavior**:
- Massive inflation from staking rewards
- Total supply increases dramatically
- Staking Dynamics chart: Exponential growth
- Circulating supply % may exceed 100% (due to reward minting)

**Use Case**: Ponzi-like tokenomics, hyperinflation scenario

**Warning**: APY > 100% is usually unsustainable

---

## Combined Edge Cases

### Edge Case 24: All Features Disabled (Tier 1 Baseline)

**Configuration**:
```json
{
  "mode": "tier1",
  "behaviors": {
    "cliff_shock": {"enabled": false},
    "price_trigger": {"enabled": false},
    "relock": {"enabled": false}
  }
}
```

**Behavior**:
- Pure deterministic vesting
- No behavioral modifications
- Baseline scenario for comparison

**Use Case**: Simplest case, testing core vesting logic

---

### Edge Case 25: All Features Enabled + Extreme Values

**Configuration**:
```json
{
  "mode": "tier3",
  "buckets": [
    {
      "allocation_pct": 100,
      "tge_unlock_pct": 50,
      "cliff_months": 12,
      "vesting_months": 24
    }
  ],
  "behaviors": {
    "cliff_shock": {
      "enabled": true,
      "cliff_shock_pct": 100,
      "cliff_shock_buckets": ["Team"]
    },
    "price_trigger": {
      "enabled": true,
      "price_source": "volatile",
      "take_profit": 1.5,
      "stop_loss": 0.7,
      "extra_sell_pct": 50
    },
    "relock": {
      "enabled": true,
      "relock_pct": 30,
      "lock_duration_months": 12
    }
  },
  "dynamic_staking": {
    "enabled": true,
    "base_apy": 0.20,
    "participation_rate": 0.60
  },
  "dynamic_pricing": {
    "enabled": true,
    "elasticity": 1.5,
    "monthly_buy_pressure": 1000000
  },
  "treasury_strategies": {
    "enabled": true,
    "distribution": {
      "buyback": 40,
      "liquidity": 40,
      "reserves": 20
    }
  }
}
```

**Behavior**:
- Complex interaction of all features
- High variance in outcomes (Tier 3 Monte Carlo)
- May produce extreme scenarios (price crash + cliff shock)

**Use Case**: Stress testing, worst-case analysis

---

### Edge Case 26: Pricing Without Staking

**Configuration**:
```json
{
  "mode": "tier2",
  "dynamic_pricing": {"enabled": true},
  "dynamic_staking": {"enabled": false}
}
```

**Behavior**:
- Price Evolution chart appears
- Staking Dynamics chart does NOT appear
- 4 charts total (not 5)

**Use Case**: Model price without staking complexity

---

### Edge Case 27: Staking Without Pricing

**Configuration**:
```json
{
  "mode": "tier2",
  "dynamic_pricing": {"enabled": false},
  "dynamic_staking": {"enabled": true}
}
```

**Behavior**:
- Staking Dynamics chart appears
- Price Evolution chart does NOT appear
- 4 charts total (not 5)
- Price for price triggers uses "scenario" source

**Use Case**: Model staking without bonding curve

---

## Validation and Normalization

### How Invalid Inputs Are Handled

The simulator uses a **two-stage approach**:

1. **Validation**: Checks for invalid inputs, returns warnings
2. **Normalization**: Fixes invalid values to safe defaults

**Example**:
```python
# User input
config = {
  "buckets": [{
    "tge_unlock_pct": 150,  # Invalid
    "cliff_months": -6       # Invalid
  }]
}

# Validation warnings
warnings = [
  "TGE unlock should be between 0 and 100",
  "cliff_months should be non-negative"
]

# Normalization
normalized_config = {
  "buckets": [{
    "tge_unlock_pct": 100,  # Clamped to max
    "cliff_months": 0        # Clamped to min
  }]
}
```

### Critical vs. Non-Critical Errors

**Critical Errors** (stop simulation):
- Total allocation > 100%
- Missing required keys (token name, buckets)
- Invalid date formats

**Non-Critical Warnings** (normalize and continue):
- Negative cliff_months → 0
- TGE unlock > 100% → 100%
- Negative values → 0 or default

---

## Testing Edge Cases

### How to Test Edge Cases

1. **Use Tier 1** for simple edge cases (faster)
2. **Export JSON** before running to save configuration
3. **Compare results** against expected behavior
4. **Check warnings** in the UI warning box
5. **Review charts** for anomalies (flat lines, spikes, negative values)

### Automated Edge Case Tests

The simulator includes automated test suite:
```bash
pytest tests/test_edge_cases.py -v
```

Covers:
- Zero supply
- Empty buckets
- 100% cliff shock
- Extreme APY
- Negative inputs
- Full Tier 2/3 integration

See `tests/test_edge_cases.py` for full test cases.

---

## Edge Case Checklist

Before finalizing your tokenomics, test these scenarios:

- [ ] All buckets unlock at TGE (0 cliff, 0 vesting)
- [ ] Long cliff with no TGE (team lockup)
- [ ] Extreme cliff shock (100% multiplier)
- [ ] Price stays flat (elasticity = 0, stable scenario)
- [ ] Price crashes (volatile + stop loss triggers)
- [ ] Zero buy pressure (bear market)
- [ ] 100% staking participation
- [ ] Zero staking participation
- [ ] All features disabled (baseline)
- [ ] All features enabled (complexity test)

---

## Real-World Edge Case Examples

### Example 1: Stablecoin Vesting

```json
{
  "token": {
    "name": "Stable Governance",
    "ticker": "SGOV",
    "total_supply": 100000000
  },
  "buckets": [
    {
      "name": "DAO Treasury",
      "allocation_pct": 100,
      "tge_unlock_pct": 10,
      "cliff_months": 0,
      "vesting_months": 48
    }
  ],
  "dynamic_pricing": {
    "enabled": true,
    "initial_price": 1.0,
    "elasticity": 0.0
  }
}
```

**Why**: Stablecoin maintains $1.00 peg, vesting spreads governance power

---

### Example 2: NFT Project Revenue Share

```json
{
  "token": {
    "name": "NFT Revenue Token",
    "ticker": "NRT",
    "total_supply": 10000
  },
  "buckets": [
    {
      "name": "Holders",
      "allocation_pct": 100,
      "tge_unlock_pct": 100,
      "cliff_months": 0,
      "vesting_months": 0
    }
  ],
  "behaviors": {
    "relock": {
      "enabled": true,
      "relock_pct": 90,
      "lock_duration_months": 12
    }
  }
}
```

**Why**: Instant distribution but holders relock for revenue claims

---

### Example 3: Deflationary Burn Model

```json
{
  "token": {
    "total_supply": 1000000000
  },
  "treasury_strategies": {
    "enabled": true,
    "distribution": {
      "buyback": 100,
      "liquidity": 0,
      "reserves": 0
    }
  }
}
```

**Why**: All treasury funds used for buyback (simulates burn)

---

## Next Steps

- See [USER_GUIDE.md](USER_GUIDE.md) for standard usage
- See [CONFIGURATION.md](CONFIGURATION.md) for parameter details
- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical implementation
