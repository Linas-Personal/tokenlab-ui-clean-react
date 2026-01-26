"""
Canonical JSON runner for vesting simulator.
Runs in isolation so PYTHONPATH determines which implementation is used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _jsonify(x: Any) -> Any:
    """Make results JSON-serializable (numpy/pandas safe)."""
    try:
        import numpy as np
        if isinstance(x, np.ndarray):
            return x.tolist()
        if isinstance(x, (np.floating, np.integer)):
            return x.item()
    except Exception:
        pass

    # pandas objects
    try:
        import pandas as pd
        if isinstance(x, pd.DataFrame):
            return x.to_dict(orient="list")
        if isinstance(x, pd.Series):
            return x.to_list()
    except Exception:
        pass

    if isinstance(x, dict):
        return {k: _jsonify(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonify(v) for v in x]
    return x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="Path to config JSON")
    ap.add_argument("--out", required=True, help="Path to write results JSON")
    args = ap.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()

    config = json.loads(config_path.read_text(encoding="utf-8"))

    # Import here so PYTHONPATH decides which implementation is used
    from tokenlab_abm.analytics.vesting_simulator import VestingSimulator

    sim = VestingSimulator(config)
    results = sim.run()

    out_path.write_text(
        json.dumps(_jsonify(results), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"✅ Results written to {out_path}")


if __name__ == "__main__":
    main()
