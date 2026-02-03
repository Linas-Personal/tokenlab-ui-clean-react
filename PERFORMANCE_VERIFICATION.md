# Performance Verification

Generated: 2026-02-03T15:33:32.401447Z

## Environment
- Python: 3.10.19
- Platform: Linux-6.12.47-x86_64-with-glibc2.39

## Scenario
- Horizon months: 36
- Buckets: Team, Seed, Community
- Tier 2 features: {"staking": true, "pricing": "bonding_curve", "treasury": true, "volume": true}
- Tier 3 features: {"cohorts": true, "monte_carlo_trials": 30}

## Results (seconds)
- tier1: 0.0119
- tier2: 0.0087
- tier3: 0.01
- monte_carlo_trials_30: 0.4137
