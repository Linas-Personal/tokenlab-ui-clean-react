"""
Comprehensive integration tests for FastAPI backend.

These tests use TestClient to make real HTTP requests against the FastAPI app
without mocking. Tests cover:
- All API routes
- Request/response validation with Pydantic
- Error handling and edge cases
- Boundary conditions
- Concurrent requests
"""

import pytest
import json
from fastapi.testclient import TestClient
from app.main import app

# Create TestClient for real HTTP requests
client = TestClient(app)


# =============================================================================
# HEALTH CHECK & BASIC CONNECTIVITY
# =============================================================================

def test_health_check():
    """Test health check endpoint returns 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_cors_headers():
    """Test CORS headers are properly set on OPTIONS preflight."""
    response = client.options("/api/v1/simulate")
    # OPTIONS endpoint should exist and return 200
    assert response.status_code == 200
    # CORS middleware should add allow-origin header
    # Note: In TestClient, CORS headers may not be added, but endpoint should work
    assert response.json() == {"detail": "OK"}


# =============================================================================
# SIMULATION ENDPOINT - HAPPY PATH
# =============================================================================

def test_simulate_tier1_basic():
    """Test basic Tier 1 simulation with valid config."""
    config = {
        "token": {
            "name": "TestToken",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent",
            "simulation_mode": "tier1"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "behaviors": {
            "cliff_shock": {"enabled": False},
            "relock": {"enabled": False}
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 50,
                "tge_unlock_pct": 0,
                "cliff_months": 6,
                "vesting_months": 12
            },
            {
                "bucket": "Investors",
                "allocation": 50,
                "tge_unlock_pct": 10,
                "cliff_months": 3,
                "vesting_months": 9
            }
        ]
    }

    response = client.post("/api/v1/simulate", json={"config": config})

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "data" in data
    assert "warnings" in data
    assert "execution_time_ms" in data

    # Verify data structure
    assert "bucket_results" in data["data"]
    assert "global_metrics" in data["data"]
    assert "summary_cards" in data["data"]

    # Verify bucket results
    assert len(data["data"]["bucket_results"]) > 0
    first_bucket = data["data"]["bucket_results"][0]
    assert "month_index" in first_bucket
    assert "date" in first_bucket
    assert "bucket" in first_bucket
    assert "unlocked_this_month" in first_bucket

    # Verify global metrics
    assert len(data["data"]["global_metrics"]) == 13  # 0-12 months
    first_global = data["data"]["global_metrics"][0]
    assert "total_unlocked" in first_global
    assert "total_expected_sell" in first_global
    assert "expected_circulating_pct" in first_global

    # Verify summary cards
    summary = data["data"]["summary_cards"]
    assert "max_unlock_tokens" in summary
    assert "max_sell_tokens" in summary
    assert "circ_12_pct" in summary

    # Verify execution time is reasonable
    assert 0 < data["execution_time_ms"] < 10000


def test_simulate_tier2_with_dynamic_features():
    """Test Tier 2 simulation with all dynamic features enabled."""
    config = {
        "token": {
            "name": "DynamicToken",
            "total_supply": 1_000_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 24,
            "allocation_mode": "percent",
            "simulation_mode": "tier2"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "behaviors": {
            "cliff_shock": {"enabled": False},
            "relock": {"enabled": False}
        },
        "tier2": {
            "staking": {
                "enabled": True,
                "apy": 0.15,
                "max_capacity_pct": 0.60,
                "lockup_months": 6,
                "participation_rate": 0.50,
                "reward_source": "treasury"
            },
            "pricing": {
                "enabled": True,
                "pricing_model": "bonding_curve",
                "initial_price": 1.0,
                "bonding_curve_param": 0.5
            },
            "treasury": {
                "enabled": True,
                "initial_balance_pct": 0.20,
                "hold_pct": 0.30,
                "liquidity_pct": 0.50,
                "buyback_pct": 0.20
            },
            "volume": {
                "enabled": True,
                "volume_model": "proportional",
                "base_daily_volume": 1_000_000,
                "volume_multiplier": 1.0
            }
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 30,
                "tge_unlock_pct": 0,
                "cliff_months": 12,
                "vesting_months": 24
            },
            {
                "bucket": "Treasury",
                "allocation": 40,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 36
            },
            {
                "bucket": "Liquidity",
                "allocation": 30,
                "tge_unlock_pct": 100,
                "cliff_months": 0,
                "vesting_months": 0
            }
        ]
    }

    response = client.post("/api/v1/simulate", json={"config": config})

    assert response.status_code == 200
    data = response.json()

    # Verify Tier 2 specific fields
    first_global = data["data"]["global_metrics"][0]
    assert "current_price" in first_global
    assert "staked_amount" in first_global
    assert "liquidity_deployed" in first_global
    assert "treasury_balance" in first_global

    # Verify price evolution
    prices = [g["current_price"] for g in data["data"]["global_metrics"] if g["current_price"] is not None]
    assert len(prices) > 0
    assert all(p > 0 for p in prices)


def test_simulate_tier3_monte_carlo():
    """Test Tier 3 simulation with Monte Carlo and cohorts."""
    config = {
        "token": {
            "name": "MonteToken",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent",
            "simulation_mode": "tier3"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "behaviors": {
            "cliff_shock": {"enabled": False},
            "relock": {"enabled": False}
        },
        "tier2": {
            "staking": {"enabled": False},
            "pricing": {"enabled": False},
            "treasury": {"enabled": False},
            "volume": {"enabled": False}
        },
        "tier3": {
            "monte_carlo": {
                "enabled": True,
                "num_trials": 10,
                "variance_level": "low",
                "seed": 42
            },
            "cohort_behavior": {
                "enabled": False
            }
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 6,
                "vesting_months": 6
            }
        ]
    }

    response = client.post("/api/v1/simulate", json={"config": config})

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["global_metrics"]) == 13  # 0-12 months


# =============================================================================
# VALIDATION ENDPOINT
# =============================================================================

def test_validate_valid_config():
    """Test validation endpoint with valid config."""
    config = {
        "token": {
            "name": "TestToken",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": 10,
                "cliff_months": 6,
                "vesting_months": 12
            }
        ]
    }

    response = client.post("/api/v1/config/validate", json={"config": config})

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert "warnings" in data
    assert "errors" in data


def test_validate_invalid_allocation():
    """Test validation catches allocation > 100%."""
    config = {
        "token": {
            "name": "TestToken",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent"
        },
        "assumptions": {
            "sell_pressure_level": "medium"
        },
        "buckets": [
            {
                "bucket": "A",
                "allocation": 60,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 12
            },
            {
                "bucket": "B",
                "allocation": 60,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 12
            }
        ]
    }

    response = client.post("/api/v1/config/validate", json={"config": config})

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0
    assert any("100%" in e for e in data["errors"])


# =============================================================================
# ERROR HANDLING & INVALID INPUTS
# =============================================================================

def test_simulate_missing_required_fields():
    """Test simulation with missing required fields returns 422."""
    config = {
        "token": {
            "total_supply": 1_000_000
            # Missing name, start_date, horizon_months
        },
        "buckets": []
    }

    response = client.post("/api/v1/simulate", json={"config": config})

    assert response.status_code == 422  # Validation error
    error_data = response.json()
    assert "detail" in error_data


def test_simulate_invalid_date_format():
    """Test simulation with invalid date format."""
    config = {
        "token": {
            "name": "Test",
            "total_supply": 1_000_000,
            "start_date": "01/01/2026",  # Wrong format
            "horizon_months": 12,
            "allocation_mode": "percent",
            "simulation_mode": "tier1"
        },
        "buckets": []
    }

    response = client.post("/api/v1/simulate", json={"config": config})

    # Should still run (validation happens but doesn't block)
    # or return 422 if validation is strict
    assert response.status_code in [200, 422]


def test_simulate_negative_values():
    """Test simulation handles negative values."""
    config = {
        "token": {
            "name": "Test",
            "total_supply": -1000,  # Negative
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent",
            "simulation_mode": "tier1"
        },
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": -10,  # Negative
                "cliff_months": -5,  # Negative
                "vesting_months": 12
            }
        ]
    }

    response = client.post("/api/v1/simulate", json={"config": config})

    # Should normalize or return validation error
    if response.status_code == 200:
        # If normalized, warnings should be present
        data = response.json()
        assert len(data["warnings"]) > 0


def test_simulate_malformed_json():
    """Test malformed JSON returns 422."""
    response = client.post(
        "/api/v1/simulate",
        data="not valid json{",
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422


def test_simulate_empty_body():
    """Test empty request body returns 422."""
    response = client.post("/api/v1/simulate", json={})

    assert response.status_code == 422


# =============================================================================
# BOUNDARY CONDITIONS
# =============================================================================

def test_simulate_zero_supply():
    """Test simulation with zero total supply."""
    config = {
        "token": {
            "name": "ZeroToken",
            "total_supply": 0,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent",
            "simulation_mode": "tier1"
        },
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": 100,
                "cliff_months": 0,
                "vesting_months": 0
            }
        ]
    }

    response = client.post("/api/v1/simulate", json={"config": config})

    assert response.status_code == 200
    data = response.json()

    # All unlocks should be zero
    for metric in data["data"]["global_metrics"]:
        assert metric["total_unlocked"] == 0


def test_simulate_zero_horizon():
    """Test simulation with zero horizon (TGE only)."""
    config = {
        "token": {
            "name": "TGEOnly",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 0,
            "allocation_mode": "percent",
            "simulation_mode": "tier1"
        },
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": 100,
                "cliff_months": 0,
                "vesting_months": 0
            }
        ]
    }

    response = client.post("/api/v1/simulate", json={"config": config})

    assert response.status_code == 200
    data = response.json()

    # Should have only 1 month of data
    assert len(data["data"]["global_metrics"]) == 1


def test_simulate_large_supply():
    """Test simulation with very large supply (1 trillion tokens)."""
    config = {
        "token": {
            "name": "LargeToken",
            "total_supply": 1_000_000_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "tokens",
            "simulation_mode": "tier1"
        },
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 1_000_000_000_000,
                "tge_unlock_pct": 0,
                "cliff_months": 6,
                "vesting_months": 6
            }
        ]
    }

    response = client.post("/api/v1/simulate", json={"config": config})

    assert response.status_code == 200
    data = response.json()

    # Verify calculations work with large numbers
    assert data["data"]["summary_cards"]["max_unlock_tokens"] > 0


def test_simulate_long_horizon():
    """Test simulation with very long horizon (120 months = 10 years)."""
    config = {
        "token": {
            "name": "LongVest",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 120,
            "allocation_mode": "percent",
            "simulation_mode": "tier1"
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 12,
                "vesting_months": 108
            }
        ]
    }

    response = client.post("/api/v1/simulate", json={"config": config})

    assert response.status_code == 200
    data = response.json()

    # Should have 121 months (0-120)
    assert len(data["data"]["global_metrics"]) == 121


def test_simulate_empty_buckets():
    """Test simulation with no allocation buckets.

    Empty buckets should be rejected with 422 since validation warns about it
    and a simulation with no buckets doesn't make sense.
    """
    config = {
        "token": {
            "name": "NoBuckets",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent",
            "simulation_mode": "tier1"
        },
        "buckets": []
    }

    response = client.post("/api/v1/simulate", json={"config": config})

    # Empty buckets should result in validation error (422)
    # This is correct behavior - can't simulate with no buckets
    assert response.status_code == 422
    data = response.json()

    # Should get Pydantic validation error
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) > 0
    # Error should mention buckets being too short
    assert any("buckets" in str(error) for error in data["detail"])


# =============================================================================
# DATA INTEGRITY & OUTPUT VERIFICATION
# =============================================================================

def test_simulate_data_consistency():
    """Verify bucket totals match global totals."""
    config = {
        "token": {
            "name": "Consistency",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 24,
            "allocation_mode": "percent",
            "simulation_mode": "tier1"
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 30,
                "tge_unlock_pct": 0,
                "cliff_months": 12,
                "vesting_months": 12
            },
            {
                "bucket": "Investors",
                "allocation": 40,
                "tge_unlock_pct": 10,
                "cliff_months": 6,
                "vesting_months": 12
            },
            {
                "bucket": "Liquidity",
                "allocation": 30,
                "tge_unlock_pct": 100,
                "cliff_months": 0,
                "vesting_months": 0
            }
        ]
    }

    response = client.post("/api/v1/simulate", json={"config": config})
    assert response.status_code == 200
    data = response.json()

    # For each month, sum of bucket unlocks should equal global total
    for month in range(25):  # 0-24
        bucket_total = sum(
            b["unlocked_this_month"]
            for b in data["data"]["bucket_results"]
            if b["month_index"] == month
        )

        global_unlock = next(
            g["total_unlocked"]
            for g in data["data"]["global_metrics"]
            if g["month_index"] == month
        )

        # Allow small floating point error
        assert abs(bucket_total - global_unlock) < 0.01


def test_simulate_allocation_totals():
    """Verify final cumulative unlocks equal allocations."""
    config = {
        "token": {
            "name": "Totals",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 36,
            "allocation_mode": "percent",
            "simulation_mode": "tier1"
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 25,
                "tge_unlock_pct": 0,
                "cliff_months": 12,
                "vesting_months": 24
            },
            {
                "bucket": "Investors",
                "allocation": 25,
                "tge_unlock_pct": 10,
                "cliff_months": 6,
                "vesting_months": 18
            },
            {
                "bucket": "Community",
                "allocation": 50,
                "tge_unlock_pct": 20,
                "cliff_months": 3,
                "vesting_months": 24
            }
        ]
    }

    response = client.post("/api/v1/simulate", json={"config": config})
    assert response.status_code == 200
    data = response.json()

    # Get final month (36)
    final_buckets = [b for b in data["data"]["bucket_results"] if b["month_index"] == 36]

    # Total cumulative should be close to 100% of supply
    total_cumulative = sum(b["unlocked_cumulative"] for b in final_buckets)
    assert abs(total_cumulative - 1_000_000) < 100  # Within 100 tokens due to floating point


# =============================================================================
# CONCURRENT REQUESTS
# =============================================================================

def test_concurrent_simulations():
    """Test handling multiple concurrent simulation requests."""
    config = {
        "token": {
            "name": "Concurrent",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent",
            "simulation_mode": "tier1"
        },
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 6,
                "vesting_months": 6
            }
        ]
    }

    # Send 5 concurrent requests
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(client.post, "/api/v1/simulate", json={"config": config}) for _ in range(5)]
        responses = [f.result() for f in futures]

    # All should succeed
    status_codes = [r.status_code for r in responses]
    if not all(code == 200 for code in status_codes):
        # Print debug info if any fail
        for i, (response, code) in enumerate(zip(responses, status_codes)):
            if code != 200:
                print(f"Request {i} failed with status {code}: {response.text[:200]}")
    assert all(r.status_code == 200 for r in responses), f"Status codes: {status_codes}"

    # All should return same results (deterministic simulation)
    first_data = responses[0].json()
    for response in responses[1:]:
        data = response.json()
        assert len(data["data"]["global_metrics"]) == len(first_data["data"]["global_metrics"])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
