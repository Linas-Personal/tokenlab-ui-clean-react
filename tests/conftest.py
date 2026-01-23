"""
Pytest configuration and fixtures for test suite.
"""

import pytest
import matplotlib.pyplot as plt


@pytest.fixture(autouse=True)
def cleanup_figures():
    """
    Automatically close all matplotlib figures after each test.

    This prevents memory leaks from accumulating open figures across test runs.
    Uses autouse=True so it applies to all tests without explicit declaration.
    """
    yield  # Run the test
    plt.close('all')  # Clean up after test
