"""
Extract method signatures from Python files.
FIXED: Uses Path.expanduser() for proper ~ expansion.
"""
from pathlib import Path
import ast
import json


def extract_methods(file_path: str) -> dict:
    """Extract all class methods and their signatures from a Python file."""
    p = Path(file_path).expanduser().resolve()

    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    tree = ast.parse(p.read_text(encoding="utf-8"))

    methods = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            cls = node.name
            methods[cls] = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    args = [a.arg for a in item.args.args]
                    methods[cls].append({
                        "name": item.name,
                        "args": args,
                        "returns": ast.unparse(item.returns) if item.returns else None
                    })
    return methods


def compare_implementations(ui_path: str, orig_path: str) -> dict:
    """Compare method signatures between two implementations."""
    print("Extracting methods from UI implementation...")
    ui_methods = extract_methods(ui_path)

    print("Extracting methods from original implementation...")
    try:
        orig_methods = extract_methods(orig_path)
    except FileNotFoundError as e:
        print(f"⚠️  Original file not found: {e}")
        print("   Showing only UI implementation methods.")
        return {"ui_only": ui_methods, "comparison": None}

    # Compare
    comparison = {}

    for cls_name in ui_methods.keys():
        comparison[cls_name] = {
            "in_both": cls_name in orig_methods,
            "differences": {}
        }

        if cls_name in orig_methods:
            ui_method_dict = {m['name']: m for m in ui_methods[cls_name]}
            orig_method_dict = {m['name']: m for m in orig_methods[cls_name]}

            # Methods only in UI
            only_ui = set(ui_method_dict.keys()) - set(orig_method_dict.keys())
            if only_ui:
                comparison[cls_name]["differences"]["new_methods"] = sorted(only_ui)

            # Methods only in original
            only_orig = set(orig_method_dict.keys()) - set(ui_method_dict.keys())
            if only_orig:
                comparison[cls_name]["differences"]["missing_methods"] = sorted(only_orig)

            # Signature differences
            sig_diffs = []
            common = set(ui_method_dict.keys()) & set(orig_method_dict.keys())
            for method in common:
                if ui_method_dict[method]['args'] != orig_method_dict[method]['args']:
                    sig_diffs.append({
                        "method": method,
                        "ui_args": ui_method_dict[method]['args'],
                        "orig_args": orig_method_dict[method]['args']
                    })
            if sig_diffs:
                comparison[cls_name]["differences"]["signature_changes"] = sig_diffs

    # Classes only in UI
    only_ui_classes = set(ui_methods.keys()) - set(orig_methods.keys())
    if only_ui_classes:
        comparison["_new_classes"] = sorted(only_ui_classes)

    # Classes only in original
    only_orig_classes = set(orig_methods.keys()) - set(ui_methods.keys())
    if only_orig_classes:
        comparison["_missing_classes"] = sorted(only_orig_classes)

    return {
        "ui_methods": ui_methods,
        "original_methods": orig_methods,
        "comparison": comparison
    }


def main():
    """Main execution."""
    import sys

    # Default paths (update these)
    ui_path = Path.home() / "tokenlab-ui-clean-react" / "src" / "tokenlab_abm" / "analytics" / "vesting_simulator.py"
    orig_path = Path.home() / "TokenLab" / "src" / "tokenlab_abm" / "analytics" / "vesting_simulator.py"

    # Allow command-line override
    if len(sys.argv) > 1:
        ui_path = Path(sys.argv[1]).expanduser().resolve()
    if len(sys.argv) > 2:
        orig_path = Path(sys.argv[2]).expanduser().resolve()

    print("=" * 70)
    print("METHOD SIGNATURE EXTRACTION & COMPARISON")
    print("=" * 70)
    print(f"UI implementation: {ui_path}")
    print(f"Original implementation: {orig_path}")
    print()

    result = compare_implementations(str(ui_path), str(orig_path))

    if result["comparison"] is None:
        # Only UI available
        print("\n📋 UI Implementation Classes:")
        for cls_name, methods in result["ui_only"].items():
            print(f"\n  {cls_name}:")
            for method in methods:
                args_str = ", ".join(method["args"])
                ret_str = f" -> {method['returns']}" if method['returns'] else ""
                print(f"    - {method['name']}({args_str}){ret_str}")
    else:
        # Full comparison
        print("\n🔍 COMPARISON RESULTS:")
        comp = result["comparison"]

        if "_new_classes" in comp:
            print(f"\n✨ New classes in UI (not in original): {comp['_new_classes']}")

        if "_missing_classes" in comp:
            print(f"\n⚠️  Missing classes from original: {comp['_missing_classes']}")

        for cls_name, info in comp.items():
            if cls_name.startswith("_"):
                continue

            print(f"\n📦 Class: {cls_name}")
            if not info["in_both"]:
                print("   ⚠️  Only in UI implementation")
                continue

            diffs = info["differences"]
            if not diffs:
                print("   ✅ Identical to original")
            else:
                if "new_methods" in diffs:
                    print(f"   ✨ New methods: {diffs['new_methods']}")
                if "missing_methods" in diffs:
                    print(f"   ⚠️  Missing methods: {diffs['missing_methods']}")
                if "signature_changes" in diffs:
                    print("   🔄 Signature changes:")
                    for sig_diff in diffs["signature_changes"]:
                        print(f"      - {sig_diff['method']}:")
                        print(f"        UI:       ({', '.join(sig_diff['ui_args'])})")
                        print(f"        Original: ({', '.join(sig_diff['orig_args'])})")

        # Save to file
        output_file = Path.home() / "method_comparison.json"
        output_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\n💾 Full comparison saved to: {output_file}")


if __name__ == "__main__":
    main()
