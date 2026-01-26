"""
Master verification runner.
Executes all verification scripts in recommended order.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def run_script(script_name: str, description: str) -> bool:
    """Run a verification script and report status."""
    script_path = Path(__file__).parent / script_name

    print("\n" + "=" * 70)
    print(f"🔍 {description}")
    print("=" * 70)

    if not script_path.exists():
        print(f"⚠️  Script not found: {script_path}")
        return False

    try:
        if script_name.endswith('.sh'):
            subprocess.check_call(['bash', str(script_path)])
        else:
            subprocess.check_call([sys.executable, str(script_path)])
        print(f"✅ {description} - COMPLETED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED (exit code {e.returncode})")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def main():
    """Run all verification scripts."""
    print("=" * 70)
    print("COMPREHENSIVE VERIFICATION SUITE")
    print("=" * 70)
    print("\nThis will run all verification scripts in recommended order.")
    print("Some tests may fail if prerequisites aren't met (e.g., original repo).")
    print("\nPress Enter to continue, Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        return

    results = []

    # 1. Backend documentation
    results.append(run_script(
        "document_backend_interface.py",
        "Backend Interface Documentation"
    ))

    # 2. Edge case testing
    results.append(run_script(
        "test_edge_cases.py",
        "Edge Case Testing"
    ))

    # 3. Contract testing
    results.append(run_script(
        "test_contracts.py",
        "Contract-Driven Integration Tests"
    ))

    # 4. Method signature extraction
    results.append(run_script(
        "extract_method_signatures.py",
        "Method Signature Comparison"
    ))

    # 5. Backend API analysis
    results.append(run_script(
        "analyze_backend_api.sh",
        "Backend API Analysis (grep)"
    ))

    # 6. Parity testing (may fail if original repo not available)
    results.append(run_script(
        "compare_parity_subprocess.py",
        "Parity Testing (Subprocess Method)"
    ))

    # Summary
    print("\n\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r)
    failed = sum(1 for r in results if not r)

    print(f"\n  Total tests: {len(results)}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")

    if failed > 0:
        print("\n  Some tests failed. This may be expected if:")
        print("    - Original TokenLab repo not cloned")
        print("    - Edge cases reveal missing validation")
        print("    - Contract schemas need updating")
        print("\n  Review individual test output above for details.")

    print("\n" + "=" * 70)

    # List output files
    home = Path.home()
    output_files = [
        "parity_config.json",
        "out_ui.json",
        "out_orig.json",
        "method_comparison.json",
        "backend_api_surface.txt",
        "backend_data_structures.txt"
    ]

    existing_outputs = [f for f in output_files if (home / f).exists()]
    if existing_outputs:
        print("\n📁 Output files created:")
        for f in existing_outputs:
            print(f"   - ~/{f}")

    print("\n✨ Verification suite complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
