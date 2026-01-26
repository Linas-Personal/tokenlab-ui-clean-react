"""
Document backend interface.
FIXED: Uses inspect.isfunction instead of inspect.ismethod for classes.
FIXED: Uses Path.expanduser() for proper ~ expansion.
"""
import inspect
import sys
from pathlib import Path


def document_vesting_simulator():
    """Document the VestingSimulator class interface."""
    # Add to path (use absolute path, not ~)
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "src"))

    from tokenlab_abm.analytics.vesting_simulator import VestingSimulator

    print("=" * 70)
    print("BACKEND INTERFACE DOCUMENTATION")
    print("=" * 70)

    print("\n📦 VestingSimulator Methods:")
    print("-" * 70)

    # FIXED: Use inspect.isfunction for class definitions
    for name, fn in inspect.getmembers(VestingSimulator, predicate=inspect.isfunction):
        if not name.startswith("_"):  # Skip private methods
            sig = inspect.signature(fn)
            print(f"  {name}{sig}")

            # Get docstring if available
            if fn.__doc__:
                doc_lines = fn.__doc__.strip().split('\n')
                first_line = doc_lines[0].strip()
                if first_line:
                    print(f"    → {first_line}")


def document_gradio_app():
    """Document the Gradio app interface."""
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))

    try:
        import apps.vesting_gradio_app as gr_app

        print("\n📱 Gradio App Functions:")
        print("-" * 70)

        # List of expected functions
        expected_functions = [
            'run_simulation',
            'add_bucket',
            'remove_bucket',
            'export_results'
        ]

        for func_name in expected_functions:
            if hasattr(gr_app, func_name):
                fn = getattr(gr_app, func_name)
                sig = inspect.signature(fn)
                print(f"  {func_name}{sig}")

                if fn.__doc__:
                    doc_lines = fn.__doc__.strip().split('\n')
                    first_line = doc_lines[0].strip()
                    if first_line:
                        print(f"    → {first_line}")
            else:
                print(f"  ⚠️  {func_name} not found")

    except ImportError as e:
        print(f"\n⚠️  Could not import Gradio app: {e}")
        print("   This is OK if you don't have a Gradio interface.")


def document_data_structures():
    """Document key data structures (configs, results)."""
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "src"))

    print("\n📋 Data Structures:")
    print("-" * 70)

    # Check if there are Pydantic models or dataclasses
    try:
        from tokenlab_abm.analytics import vesting_simulator
        import ast

        # Parse the file to find class definitions
        file_path = Path(vesting_simulator.__file__)
        tree = ast.parse(file_path.read_text(encoding="utf-8"))

        config_classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                if 'config' in class_name.lower() or 'result' in class_name.lower():
                    config_classes.append(class_name)

        if config_classes:
            print(f"  Found data structure classes: {', '.join(config_classes)}")
        else:
            print("  No explicit config/result classes found (may use dicts)")

    except Exception as e:
        print(f"  Could not analyze: {e}")


def main():
    """Main execution."""
    document_vesting_simulator()
    document_gradio_app()
    document_data_structures()

    print("\n" + "=" * 70)
    print("✅ Documentation complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
