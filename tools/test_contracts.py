"""
Contract-driven testing for backend-frontend integration.
Validates that backend outputs match expected schemas.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

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


def validate_schema(data: dict, schema: dict, path: str = "") -> list[str]:
    """
    Simple schema validation (subset of JSON Schema).
    Returns list of validation errors.
    """
    errors = []

    # Check required fields
    if "required" in schema:
        for field in schema["required"]:
            if field not in data:
                errors.append(f"{path}: Missing required field '{field}'")

    # Check properties
    if "properties" in schema:
        for field, field_schema in schema["properties"].items():
            if field in data:
                field_path = f"{path}.{field}" if path else field
                field_errors = validate_field(data[field], field_schema, field_path)
                errors.extend(field_errors)

    return errors


def validate_field(value: Any, schema: dict, path: str) -> list[str]:
    """Validate a single field against its schema."""
    errors = []

    # Type checking
    expected_type = schema.get("type")
    if expected_type:
        if expected_type == "object" and not isinstance(value, dict):
            errors.append(f"{path}: Expected object, got {type(value).__name__}")
        elif expected_type == "array" and not isinstance(value, list):
            errors.append(f"{path}: Expected array, got {type(value).__name__}")
        elif expected_type == "string" and not isinstance(value, str):
            errors.append(f"{path}: Expected string, got {type(value).__name__}")
        elif expected_type == "number" and not isinstance(value, (int, float)):
            errors.append(f"{path}: Expected number, got {type(value).__name__}")

    # Recursive validation for objects
    if expected_type == "object" and isinstance(value, dict):
        errors.extend(validate_schema(value, schema, path))

    # Array item validation
    if expected_type == "array" and isinstance(value, list):
        if "items" in schema:
            for i, item in enumerate(value):
                item_errors = validate_field(item, schema["items"], f"{path}[{i}]")
                errors.extend(item_errors)

    return errors


def run_contract_test(config_file: Path, schema_file: Path) -> dict:
    """Run a contract test: load config, run simulator, validate output."""
    from tokenlab_abm.analytics.vesting_simulator import VestingSimulator

    print(f"\n{'='*70}")
    print(f"Testing: {config_file.name}")
    print(f"{'='*70}")

    # Load config
    config = json.loads(config_file.read_text(encoding="utf-8"))
    print(f"  Config: {config.get('token_name')} (Tier {config.get('tier')})")

    # Run simulator
    try:
        sim = VestingSimulator(config)
        result = sim.run()
        print("  ✅ Simulation completed")
    except Exception as e:
        print(f"  ❌ Simulation failed: {e}")
        return {
            "config": config_file.name,
            "status": "FAILED",
            "error": str(e),
            "validation_errors": []
        }

    # Load schema
    schema = json.loads(schema_file.read_text(encoding="utf-8"))

    # Validate output
    validation_errors = validate_schema(result, schema)

    if validation_errors:
        print(f"  ❌ Schema validation failed ({len(validation_errors)} errors):")
        for error in validation_errors[:5]:  # Show first 5
            print(f"     - {error}")
        if len(validation_errors) > 5:
            print(f"     ... and {len(validation_errors) - 5} more")
        status = "FAILED"
    else:
        print("  ✅ Schema validation passed")
        status = "PASSED"

    return {
        "config": config_file.name,
        "status": status,
        "error": None,
        "validation_errors": validation_errors
    }


def main():
    """Main execution."""
    setup_paths()

    root = Path(__file__).resolve().parent.parent
    contracts_dir = root / "contracts"
    requests_dir = contracts_dir / "requests"
    responses_dir = contracts_dir / "responses"

    print("=" * 70)
    print("CONTRACT-DRIVEN INTEGRATION TESTS")
    print("=" * 70)

    # Find all request configs
    request_files = sorted(requests_dir.glob("*.json"))
    if not request_files:
        print(f"\n⚠️  No request configs found in {requests_dir}")
        print("   Create JSON files in contracts/requests/ to test")
        return

    # Use the expected schema
    schema_file = responses_dir / "expected_schema.json"
    if not schema_file.exists():
        print(f"\n⚠️  Schema file not found: {schema_file}")
        print("   Create expected_schema.json in contracts/responses/")
        return

    print(f"\nFound {len(request_files)} test configs")
    print(f"Using schema: {schema_file.name}\n")

    # Run tests
    results = []
    for config_file in request_files:
        result = run_contract_test(config_file, schema_file)
        results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r["status"] == "PASSED")
    failed = sum(1 for r in results if r["status"] == "FAILED")

    print(f"\n  Total: {len(results)}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")

    if failed > 0:
        print("\n  Failed tests:")
        for r in results:
            if r["status"] == "FAILED":
                print(f"    - {r['config']}")
                if r["error"]:
                    print(f"      Error: {r['error']}")
                if r["validation_errors"]:
                    print(f"      Validation errors: {len(r['validation_errors'])}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
