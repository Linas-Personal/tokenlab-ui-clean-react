"""
Pytest configuration and fixtures for test suite.
"""

import sys
from pathlib import Path

import pytest
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.is_dir():
    sys.path.insert(0, str(SRC_PATH))


@pytest.fixture(autouse=True)
def cleanup_figures():
    """
    Automatically close all matplotlib figures after each test.

    This prevents memory leaks from accumulating open figures across test runs.
    Uses autouse=True so it applies to all tests without explicit declaration.
    """
    yield  # Run the test
    plt.close('all')  # Clean up after test
