"""
Subprocess-based parity comparison between implementations.
Runs each simulator in a separate Python process to avoid module caching issues.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import numpy as np


# IMPORTANT: Update these paths to your actual repository locations
UI_REPO = Path.home() / "tokenlab-ui-clean-react"
ORIG_REPO = Path.home() / "TokenLab"  # Original TokenLab repo (if available)

# Python executables (use system python if no venvs)
UI_PY = sys.executable  # For now, use current interpreter
ORIG_PY = sys.executable  # Update if you have separate venvs

RUNNER_REL = Path("tools/run_vesting_sim.py")

# Test artifacts
CONFIG_JSON = Path.home() / "parity_config.json"
OUT_UI = Path.home() / "out_ui.json"
OUT_ORIG = Path.home() / "out_orig.json"


def load(p: Path) -> Any:
    """Load JSON from file."""
    return json.loads(p.read_text(encoding="utf-8"))


def create_test_config() -> None:
    """Create a standard test configuration."""
    config = {
        "token_name": "TestToken",
        "ticker": "TEST",
        "total_supply": 1_000_000_000,
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
        ]
    }
    CONFIG_JSON.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"✅ Test config created: {CONFIG_JSON}")


def run_ui_version() -> None:
    """Run the UI version of the simulator."""
    if not UI_REPO.exists():
        raise FileNotFoundError(f"UI repo not found: {UI_REPO}")

    runner = UI_REPO / RUNNER_REL
    if not runner.exists():
        raise FileNotFoundError(f"Runner script not found: {runner}")

    env = {**dict(os.environ)}  # noqa
    env["PYTHONPATH"] = str(UI_REPO / "src")

    print(f"\n🔄 Running UI version from {UI_REPO}...")
    subprocess.check_call([
        str(UI_PY),
        str(runner),
        "--config", str(CONFIG_JSON),
        "--out", str(OUT_UI),
    ], env=env)
    print(f"✅ UI results: {OUT_UI}")


def run_original_version() -> None:
    """Run the original TokenLab version (if available)."""
    if not ORIG_REPO.exists():
        print(f"⚠️  Original TokenLab repo not found: {ORIG_REPO}")
        print("   Skipping original version comparison.")
        print("   If you want to compare with original TokenLab:")
        print(f"   1. Clone it: git clone https://github.com/stelios12312312/TokenLab.git {ORIG_REPO}")
        print(f"   2. Copy tools/run_vesting_sim.py to that repo")
        print(f"   3. Re-run this script")
        return False

    runner = ORIG_REPO / RUNNER_REL
    if not runner.exists():
        print(f"⚠️  Runner script not found in original repo: {runner}")
        print(f"   Copy tools/run_vesting_sim.py to {ORIG_REPO / 'tools'}")
        return False

    import os
    env = {**dict(os.environ)}
    env["PYTHONPATH"] = str(ORIG_REPO / "src")

    print(f"\n🔄 Running original version from {ORIG_REPO}...")
    try:
        subprocess.check_call([
            str(ORIG_PY),
            str(runner),
            "--config", str(CONFIG_JSON),
            "--out", str(OUT_ORIG),
        ], env=env)
        print(f"✅ Original results: {OUT_ORIG}")
        return True
    except Exception as e:
        print(f"❌ Error running original version: {e}")
        return False


def compare(x: Any, y: Any, path: str = "") -> None:
    """Deep comparison with numeric tolerance."""
    if isinstance(x, dict) and isinstance(y, dict):
        if x.keys() != y.keys():
            only_x = sorted(set(x) - set(y))
            only_y = sorted(set(y) - set(x))
            raise AssertionError(
                f"Key mismatch at {path}:\n"
                f"  Only in first: {only_x}\n"
                f"  Only in second: {only_y}"
            )
        for k in x:
            compare(x[k], y[k], f"{path}.{k}" if path else k)
        return

    if isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y):
            raise AssertionError(
                f"Length mismatch at {path}: {len(x)} vs {len(y)}"
            )
        for i, (xi, yi) in enumerate(zip(x, y)):
            compare(xi, yi, f"{path}[{i}]")
        return

    # numeric tolerance
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        np.testing.assert_allclose(
            x, y, rtol=1e-6, atol=1e-9,
            err_msg=f"Mismatch at {path}"
        )
        return

    if x != y:
        raise AssertionError(f"Mismatch at {path}: {x!r} vs {y!r}")


def compare_outputs() -> None:
    """Compare the two output files."""
    if not OUT_UI.exists():
        raise FileNotFoundError(f"UI output not found: {OUT_UI}")

    if not OUT_ORIG.exists():
        print("\n⚠️  Original output not found, skipping comparison")
        print(f"   UI output available at: {OUT_UI}")
        return

    print("\n🔍 Comparing outputs...")
    a = load(OUT_UI)
    b = load(OUT_ORIG)

    try:
        compare(a, b)
        print("✅ Parity check PASSED (outputs match within tolerance)")
    except AssertionError as e:
        print(f"❌ Parity check FAILED:\n{e}")
        print("\n💡 Tip: This may indicate:")
        print("   1. Different algorithm implementations")
        print("   2. Different default assumptions")
        print("   3. Bug in one implementation")
        print("\nTo investigate:")
        print(f"   - Review UI output: {OUT_UI}")
        print(f"   - Review original output: {OUT_ORIG}")
        print("   - Use a JSON diff tool to see exact differences")


def main() -> None:
    """Main execution."""
    import os  # Import here for env usage

    print("=" * 70)
    print("PARITY VERIFICATION (Subprocess Method)")
    print("=" * 70)

    # Step 1: Create test config
    create_test_config()

    # Step 2: Run UI version
    run_ui_version()

    # Step 3: Run original version (if available)
    has_original = run_original_version()

    # Step 4: Compare outputs
    if has_original:
        compare_outputs()
    else:
        print("\n✅ UI version ran successfully")
        print(f"   Output: {OUT_UI}")
        print("\n💡 To enable full parity comparison:")
        print("   1. Clone original TokenLab")
        print("   2. Set up the runner script")
        print("   3. Re-run this script")


if __name__ == "__main__":
    main()
