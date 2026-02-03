"""
Edge case testing script.
Tests various edge cases that commonly expose bugs.
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def setup_paths():
    """Add project to path."""
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "src"))


def test_edge_cases():
    """Test edge cases that commonly expose bugs."""
    from tokenlab_abm.analytics.vesting_simulator import VestingSimulator

    test_cases = [
        # Edge case 1: Zero allocation
        {
            "name": "Zero Allocation",
            "config": {
                "token_name": "Test",
                "ticker": "TEST",
                "total_supply": 1000000,
                "launch_date": "2025-01-01",
                "simulation_months": 12,
                "tier": 1,
                "buckets": [
                    {
                        "name": "Team",
                        "allocation_pct": 0.0,
                        "tge_unlock_pct": 0.0,
                        "cliff_months": 0,
                        "vesting_months": 12
                    }
                ]
            }
        },
        # Edge case 2: 100% TGE unlock
        {
            "name": "100% TGE Unlock",
            "config": {
                "token_name": "Test",
                "ticker": "TEST",
                "total_supply": 1000000,
                "launch_date": "2025-01-01",
                "simulation_months": 12,
                "tier": 1,
                "buckets": [
                    {
                        "name": "Team",
                        "allocation_pct": 100.0,
                        "tge_unlock_pct": 100.0,
                        "cliff_months": 0,
                        "vesting_months": 0
                    }
                ]
            }
        },
        # Edge case 3: Very long vesting
        {
            "name": "Long Vesting (240 months)",
            "config": {
                "token_name": "Test",
                "ticker": "TEST",
                "total_supply": 1000000,
                "launch_date": "2025-01-01",
                "simulation_months": 240,
                "tier": 1,
                "buckets": [
                    {
                        "name": "Team",
                        "allocation_pct": 100.0,
                        "tge_unlock_pct": 0.0,
                        "cliff_months": 0,
                        "vesting_months": 240
                    }
                ]
            }
        },
        # Edge case 4: Multiple overlapping buckets
        {
            "name": "Multiple Overlapping Buckets",
            "config": {
                "token_name": "Test",
                "ticker": "TEST",
                "total_supply": 1000000,
                "launch_date": "2025-01-01",
                "simulation_months": 60,
                "tier": 1,
                "buckets": [
                    {
                        "name": "Team",
                        "allocation_pct": 20.0,
                        "tge_unlock_pct": 0.0,
                        "cliff_months": 12,
                        "vesting_months": 36
                    },
                    {
                        "name": "Investors",
                        "allocation_pct": 30.0,
                        "tge_unlock_pct": 10.0,
                        "cliff_months": 6,
                        "vesting_months": 24
                    },
                    {
                        "name": "Community",
                        "allocation_pct": 50.0,
                        "tge_unlock_pct": 5.0,
                        "cliff_months": 0,
                        "vesting_months": 48
                    }
                ]
            }
        },
        # Edge case 5: Allocation sum != 100%
        {
            "name": "Allocation Sum != 100%",
            "config": {
                "token_name": "Test",
                "ticker": "TEST",
                "total_supply": 1000000,
                "launch_date": "2025-01-01",
                "simulation_months": 12,
                "tier": 1,
                "buckets": [
                    {
                        "name": "Team",
                        "allocation_pct": 60.0,
                        "tge_unlock_pct": 0.0,
                        "cliff_months": 12,
                        "vesting_months": 36
                    },
                    {
                        "name": "Investors",
                        "allocation_pct": 20.0,
                        "tge_unlock_pct": 10.0,
                        "cliff_months": 6,
                        "vesting_months": 24
                    }
                ]
            }
        },
        # Edge case 6: Invalid date format
        {
            "name": "Invalid Date Format",
            "config": {
                "token_name": "Test",
                "ticker": "TEST",
                "total_supply": 1000000,
                "launch_date": "2025-13-45",  # Invalid date
                "simulation_months": 12,
                "tier": 1,
                "buckets": [
                    {
                        "name": "Team",
                        "allocation_pct": 100.0,
                        "tge_unlock_pct": 0.0,
                        "cliff_months": 0,
                        "vesting_months": 12
                    }
                ]
            }
        },
        # Edge case 7: Negative values
        {
            "name": "Negative Months",
            "config": {
                "token_name": "Test",
                "ticker": "TEST",
                "total_supply": 1000000,
                "launch_date": "2025-01-01",
                "simulation_months": 12,
                "tier": 1,
                "buckets": [
                    {
                        "name": "Team",
                        "allocation_pct": 100.0,
                        "tge_unlock_pct": 0.0,
                        "cliff_months": -6,  # Invalid
                        "vesting_months": 12
                    }
                ]
            }
        },
        # Edge case 8: Zero simulation months
        {
            "name": "Zero Simulation Months",
            "config": {
                "token_name": "Test",
                "ticker": "TEST",
                "total_supply": 1000000,
                "launch_date": "2025-01-01",
                "simulation_months": 0,
                "tier": 1,
                "buckets": [
                    {
                        "name": "Team",
                        "allocation_pct": 100.0,
                        "tge_unlock_pct": 10.0,
                        "cliff_months": 0,
                        "vesting_months": 12
                    }
                ]
            }
        }
    ]

    results = []
    for test_case in test_cases:
        try:
            sim = VestingSimulator(test_case["config"])
            result = sim.run()
            results.append({
                "test": test_case["name"],
                "status": "✅ PASS",
                "error": None
            })
        except Exception as e:
            results.append({
                "test": test_case["name"],
                "status": "❌ FAIL",
                "error": str(e),
                "traceback": traceback.format_exc()
            })

    # Print results
    print("=" * 70)
    print("EDGE CASE TESTING RESULTS")
    print("=" * 70)

    passed = sum(1 for r in results if "PASS" in r["status"])
    failed = sum(1 for r in results if "FAIL" in r["status"])

    for result in results:
        print(f"\n{result['status']} {result['test']}")
        if result['error']:
            print(f"   Error: {result['error']}")
            # Show first 300 chars of traceback
            tb_preview = result['traceback'][:300]
            print(f"   Trace: {tb_preview}...")

    print("\n" + "=" * 70)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed > 0:
        print("\n💡 Failed tests may indicate:")
        print("   - Missing input validation")
        print("   - Edge cases not handled")
        print("   - Assumptions about valid inputs")
        print("\n   Consider adding validation or better error messages.")



def main():
    """Main execution."""
    setup_paths()
    test_edge_cases()


if __name__ == "__main__":
    main()
