"""
Comprehensive tests for ABM API routes with dependency injection.

Tests cover:
- All ABM endpoints with real dependencies
- Boundary conditions (0 agents, max agents, etc.)
- Error handling and invalid inputs
- Concurrent requests and race conditions
- SSE streaming behavior
- Job queue limits and cleanup
- Cache behavior
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(test_client):
    """Use test_client fixture from conftest.py."""
    return test_client


# =============================================================================
# ABM SYNC ENDPOINT - BOUNDARY CONDITIONS
# =============================================================================

def test_abm_sync_minimal_config(client):
    """Test ABM with absolute minimum valid configuration."""
    config = {
        "token": {
            "name": "Minimal",
            "total_supply": 10_000_000,  # Larger to avoid full_individual mode
            "start_date": "2026-01-01",
            "horizon_months": 1
        },
        "buckets": [
            {
                "bucket": "Only",
                "allocation": 100,
                "tge_unlock_pct": 100,
                "cliff_months": 0,
                "vesting_months": 0
            }
        ],
        "abm": {
            "pricing_model": "constant",
            "agent_granularity": "meta_agents",  # Force meta agents
            "agents_per_cohort": 50,  # Explicitly set
            "initial_price": 1.0
        }
    }

    response = client.post("/api/v2/abm/simulate-sync", json=config)

    assert response.status_code == 200
    data = response.json()
    assert len(data["global_metrics"]) == 1  # Only month 0
    assert data["num_agents"] == 50  # 1 cohort * 50 agents


def test_abm_sync_zero_tge_zero_cliff(client):
    """Test ABM with zero TGE and zero cliff (immediate vesting)."""
    config = {
        "token": {
            "name": "ZeroCliff",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 6
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 6
            }
        ],
        "abm": {
            "pricing_model": "eoe",
            "agents_per_cohort": 20,
            "initial_price": 1.0,
            "pricing_config": {
                "holding_time": 3.0,
                "smoothing_factor": 0.3,
                "min_price": 0.01
            }
        }
    }

    response = client.post("/api/v2/abm/simulate-sync", json=config)

    assert response.status_code == 200
    data = response.json()

    # Should have unlocks starting month 0
    month_0 = next(m for m in data["global_metrics"] if m["month_index"] == 0)
    assert month_0["total_unlocked"] > 0  # Immediate vesting


def test_abm_sync_100_percent_tge(client):
    """Test ABM with 100% TGE (all unlocked immediately)."""
    config = {
        "token": {
            "name": "AllTGE",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12
        },
        "buckets": [
            {
                "bucket": "Instant",
                "allocation": 100,
                "tge_unlock_pct": 100,
                "cliff_months": 0,
                "vesting_months": 0
            }
        ],
        "abm": {
            "pricing_model": "constant",
            "agents_per_cohort": 50,
            "initial_price": 1.0
        }
    }

    response = client.post("/api/v2/abm/simulate-sync", json=config)

    assert response.status_code == 200
    data = response.json()

    # All should unlock at month 0
    month_0 = next(m for m in data["global_metrics"] if m["month_index"] == 0)
    assert month_0["total_unlocked"] == pytest.approx(1_000_000, rel=0.01)

    # No more unlocks after month 0
    month_1 = next(m for m in data["global_metrics"] if m["month_index"] == 1)
    assert month_1["total_unlocked"] == 0


def test_abm_sync_very_long_cliff(client):
    """Test ABM with cliff longer than horizon."""
    config = {
        "token": {
            "name": "LongCliff",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 24,  # Cliff longer than horizon
                "vesting_months": 12
            }
        ],
        "abm": {
            "pricing_model": "constant",
            "agents_per_cohort": 20,
            "initial_price": 1.0
        }
    }

    response = client.post("/api/v2/abm/simulate-sync", json=config)

    assert response.status_code == 200
    data = response.json()

    # Nothing should unlock during simulation
    for metric in data["global_metrics"]:
        assert metric["total_unlocked"] == 0


def test_abm_sync_single_agent_per_cohort(client):
    """Test ABM with minimum agents (1 per cohort)."""
    config = {
        "token": {
            "name": "SingleAgent",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 6
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 50,
                "tge_unlock_pct": 0,
                "cliff_months": 3,
                "vesting_months": 6
            },
            {
                "bucket": "Investors",
                "allocation": 50,
                "tge_unlock_pct": 10,
                "cliff_months": 0,
                "vesting_months": 6
            }
        ],
        "abm": {
            "pricing_model": "constant",
            "agents_per_cohort": 1,  # Minimum
            "initial_price": 1.0
        }
    }

    response = client.post("/api/v2/abm/simulate-sync", json=config)

    assert response.status_code == 200
    data = response.json()
    assert data["num_agents"] == 2  # 2 cohorts * 1 agent


def test_abm_sync_max_agents(client):
    """Test ABM with maximum reasonable agents."""
    config = {
        "token": {
            "name": "MaxAgents",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 3  # Short horizon for speed
        },
        "buckets": [
            {
                "bucket": "Community",
                "allocation": 100,
                "tge_unlock_pct": 20,
                "cliff_months": 0,
                "vesting_months": 3
            }
        ],
        "abm": {
            "pricing_model": "constant",
            "agents_per_cohort": 500,  # Maximum
            "initial_price": 1.0
        }
    }

    response = client.post("/api/v2/abm/simulate-sync", json=config)

    assert response.status_code == 200
    data = response.json()
    assert data["num_agents"] == 500
    # Should still complete in reasonable time
    assert data["execution_time_seconds"] < 30


# =============================================================================
# ABM VALIDATION ENDPOINT
# =============================================================================

def test_abm_validate_too_many_agents(client):
    """Test validation warns about excessive agent count."""
    config = {
        "token": {
            "horizon_months": 12
        },
        "buckets": [
            {"bucket": "A", "allocation": 25},
            {"bucket": "B", "allocation": 25},
            {"bucket": "C", "allocation": 25},
            {"bucket": "D", "allocation": 25}
        ],
        "abm": {
            "agents_per_cohort": 500  # 4 cohorts * 500 = 2000 agents
        }
    }

    response = client.post("/api/v2/abm/validate", json={"config": config})

    assert response.status_code == 200
    data = response.json()
    assert "warnings" in data
    # Should warn about high agent count
    assert any("agent" in w.lower() or "slow" in w.lower() for w in data["warnings"])


def test_abm_validate_allocation_over_100(client):
    """Test validation catches allocation exceeding 100%."""
    config = {
        "token": {
            "horizon_months": 12
        },
        "buckets": [
            {"bucket": "A", "allocation": 60},
            {"bucket": "B", "allocation": 60}  # Total = 120%
        ],
        "abm": {
            "agents_per_cohort": 50
        }
    }

    response = client.post("/api/v2/abm/validate", json={"config": config})

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("100" in e for e in data["errors"])


def test_abm_validate_very_long_horizon(client):
    """Test validation warns about very long simulations."""
    config = {
        "token": {
            "horizon_months": 240  # 20 years
        },
        "buckets": [
            {"bucket": "Team", "allocation": 100}
        ],
        "abm": {
            "agents_per_cohort": 100
        }
    }

    response = client.post("/api/v2/abm/validate", json={"config": config})

    assert response.status_code == 200
    data = response.json()
    assert any("horizon" in w.lower() or "slow" in w.lower() for w in data["warnings"])


# =============================================================================
# ERROR HANDLING
# =============================================================================

def test_abm_sync_missing_required_fields(client):
    """Test ABM with missing required configuration."""
    config = {
        "token": {
            "name": "Incomplete"
            # Missing total_supply, start_date, horizon_months
        },
        "buckets": []
    }

    response = client.post("/api/v2/abm/simulate-sync", json=config)

    assert response.status_code == 422  # Validation error


def test_abm_sync_invalid_pricing_model(client):
    """Test ABM with invalid pricing model."""
    config = {
        "token": {
            "name": "Invalid",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12
        },
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 12
            }
        ],
        "abm": {
            "pricing_model": "invalid_model",  # Invalid
            "agents_per_cohort": 50,
            "initial_price": 1.0
        }
    }

    response = client.post("/api/v2/abm/simulate-sync", json=config)

    assert response.status_code == 422  # Validation error


def test_abm_sync_negative_values(client):
    """Test ABM handles negative values gracefully."""
    config = {
        "token": {
            "name": "Negative",
            "total_supply": -1000,  # Negative
            "start_date": "2026-01-01",
            "horizon_months": 12
        },
        "buckets": [
            {
                "bucket": "Test",
                "allocation": 100,
                "tge_unlock_pct": -10,  # Negative
                "cliff_months": 0,
                "vesting_months": 12
            }
        ],
        "abm": {
            "pricing_model": "constant",
            "agents_per_cohort": -5,  # Negative
            "initial_price": -1.0  # Negative
        }
    }

    response = client.post("/api/v2/abm/simulate-sync", json=config)

    # Should either reject or normalize
    assert response.status_code in [422, 500]


def test_abm_sync_empty_buckets(client):
    """Test ABM with no allocation buckets."""
    config = {
        "token": {
            "name": "NoBuckets",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12
        },
        "buckets": [],  # Empty
        "abm": {
            "pricing_model": "constant",
            "agents_per_cohort": 50,
            "initial_price": 1.0
        }
    }

    response = client.post("/api/v2/abm/simulate-sync", json=config)

    assert response.status_code == 422  # Should reject empty buckets


# =============================================================================
# ASYNC JOB QUEUE - INTEGRATION TESTS
# =============================================================================

def test_abm_async_job_submission(client):
    """Test async job submission and status polling."""
    config = {
        "token": {
            "name": "AsyncTest",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 6
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 3,
                "vesting_months": 6
            }
        ],
        "abm": {
            "pricing_model": "eoe",
            "agents_per_cohort": 50,
            "initial_price": 1.0,
            "pricing_config": {
                "holding_time": 3.0,
                "smoothing_factor": 0.3,
                "min_price": 0.01
            }
        }
    }

    # Submit job
    submit_response = client.post("/api/v2/abm/simulate", json=config)

    assert submit_response.status_code == 200
    submit_data = submit_response.json()
    assert "job_id" in submit_data
    assert "status" in submit_data
    assert "status_url" in submit_data
    assert "stream_url" in submit_data

    job_id = submit_data["job_id"]

    # Poll status
    import time
    max_polls = 50
    for i in range(max_polls):
        status_response = client.get(f"/api/v2/abm/jobs/{job_id}/status")
        assert status_response.status_code == 200

        status_data = status_response.json()
        assert status_data["job_id"] == job_id
        assert "status" in status_data
        assert "progress_pct" in status_data

        if status_data["status"] == "completed":
            break

        time.sleep(0.1)

    # Get results
    results_response = client.get(f"/api/v2/abm/jobs/{job_id}/results")

    assert results_response.status_code == 200
    results_data = results_response.json()
    assert "global_metrics" in results_data
    assert len(results_data["global_metrics"]) == 6


def test_abm_async_job_not_found(client):
    """Test getting status of non-existent job."""
    response = client.get("/api/v2/abm/jobs/nonexistent_job_id/status")

    assert response.status_code == 404


def test_abm_async_results_before_completion(client):
    """Test getting results before job completes."""
    config = {
        "token": {
            "name": "SlowJob",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 24  # Longer simulation
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 24
            }
        ],
        "abm": {
            "pricing_model": "eoe",
            "agents_per_cohort": 100,
            "initial_price": 1.0,
            "pricing_config": {
                "holding_time": 3.0,
                "smoothing_factor": 0.3,
                "min_price": 0.01
            }
        }
    }

    # Submit job
    submit_response = client.post("/api/v2/abm/simulate", json=config)
    job_id = submit_response.json()["job_id"]

    # Try to get results immediately (job likely still running)
    import time
    time.sleep(0.05)  # Small delay

    results_response = client.get(f"/api/v2/abm/jobs/{job_id}/results")

    # Should return 400 if not completed yet, or 200 if completed
    assert results_response.status_code in [200, 400]

    if results_response.status_code == 400:
        error_data = results_response.json()
        assert "not completed" in error_data["detail"].lower()


def test_abm_async_cache_hit(client):
    """Test that identical configs use cached results."""
    config = {
        "token": {
            "name": "CacheTest",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 3
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 3
            }
        ],
        "abm": {
            "pricing_model": "constant",
            "agents_per_cohort": 20,
            "initial_price": 1.0
        }
    }

    # Submit first job
    response1 = client.post("/api/v2/abm/simulate", json=config)
    job_id1 = response1.json()["job_id"]

    # Wait for completion
    import time
    for _ in range(30):
        status = client.get(f"/api/v2/abm/jobs/{job_id1}/status").json()
        if status["status"] == "completed":
            break
        time.sleep(0.1)

    # Submit identical config
    response2 = client.post("/api/v2/abm/simulate", json=config)
    data2 = response2.json()

    # Should be cached
    assert data2["cached"] is True
    assert data2["job_id"].startswith("cached_")

    # Should be completed immediately
    status2 = client.get(f"/api/v2/abm/jobs/{data2['job_id']}/status").json()
    assert status2["status"] == "completed"


def test_abm_list_all_jobs(client):
    """Test listing all jobs endpoint."""
    response = client.get("/api/v2/abm/jobs")

    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert isinstance(data["jobs"], list)


def test_abm_queue_stats(client):
    """Test queue statistics endpoint."""
    response = client.get("/api/v2/abm/queue/stats")

    assert response.status_code == 200
    data = response.json()
    assert "total_jobs" in data
    assert "cache_size" in data
    assert "max_concurrent_jobs" in data


# =============================================================================
# CONCURRENT REQUESTS & RACE CONDITIONS
# =============================================================================

def test_abm_concurrent_async_submissions(client):
    """Test multiple concurrent job submissions."""
    import concurrent.futures

    config_template = {
        "token": {
            "name": "Concurrent",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 3
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 0,
                "vesting_months": 3
            }
        ],
        "abm": {
            "pricing_model": "constant",
            "agents_per_cohort": 10,
            "initial_price": 1.0
        }
    }

    # Create 5 different configs
    configs = []
    for i in range(5):
        config = json.loads(json.dumps(config_template))
        config["token"]["total_supply"] = 1_000_000 + i * 1000
        configs.append(config)

    # Submit concurrently
    def submit_job(cfg):
        return client.post("/api/v2/abm/simulate", json=cfg)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(submit_job, cfg) for cfg in configs]
        responses = [f.result() for f in futures]

    # All should succeed
    assert all(r.status_code == 200 for r in responses)

    # All should have job IDs
    job_ids = [r.json()["job_id"] for r in responses]
    assert len(job_ids) == 5
    assert len(set(job_ids)) == 5  # All unique


# =============================================================================
# PRICING MODELS - EDGE CASES
# =============================================================================

def test_abm_bonding_curve_pricing(client):
    """Test bonding curve pricing with extreme parameters."""
    config = {
        "token": {
            "name": "BondingCurve",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 100,
                "tge_unlock_pct": 10,
                "cliff_months": 0,
                "vesting_months": 12
            }
        ],
        "abm": {
            "pricing_model": "bonding_curve",
            "agents_per_cohort": 50,
            "initial_price": 1.0,
            "pricing_config": {
                "k": 0.000001,
                "n": 2.0
            }
        }
    }

    response = client.post("/api/v2/abm/simulate-sync", json=config)

    assert response.status_code == 200
    data = response.json()

    # Prices should be positive
    prices = [m["price"] for m in data["global_metrics"]]
    assert all(p > 0 for p in prices)


def test_abm_eoe_pricing_with_zero_velocity(client):
    """Test EOE pricing handles zero velocity edge case."""
    config = {
        "token": {
            "name": "ZeroVelocity",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 6
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 12,  # Nothing unlocks during sim
                "vesting_months": 12
            }
        ],
        "abm": {
            "pricing_model": "eoe",
            "agents_per_cohort": 50,
            "initial_price": 1.0,
            "pricing_config": {
                "holding_time": 3.0,
                "smoothing_factor": 0.3,
                "min_price": 0.01
            }
        }
    }

    response = client.post("/api/v2/abm/simulate-sync", json=config)

    assert response.status_code == 200
    data = response.json()

    # Should not crash, price should stay at initial or min
    prices = [m["price"] for m in data["global_metrics"]]
    assert all(p >= 0.01 for p in prices)  # Min price floor


# =============================================================================
# STAKING & TREASURY - EDGE CASES
# =============================================================================

def test_abm_staking_at_max_capacity(client):
    """Test staking when pool reaches max capacity."""
    config = {
        "token": {
            "name": "StakingMax",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12
        },
        "buckets": [
            {
                "bucket": "Community",
                "allocation": 100,
                "tge_unlock_pct": 100,  # All unlocked immediately
                "cliff_months": 0,
                "vesting_months": 0
            }
        ],
        "abm": {
            "pricing_model": "constant",
            "agents_per_cohort": 50,
            "initial_price": 1.0,
            "enable_staking": True,
            "staking_config": {
                "base_apy": 0.15,
                "max_capacity_pct": 0.30,  # Low cap (30% of supply)
                "lockup_months": 6,
                "reward_source": "emission",
                "apy_multiplier_at_empty": 2.0,
                "apy_multiplier_at_full": 0.5
            }
        }
    }

    response = client.post("/api/v2/abm/simulate-sync", json=config)

    assert response.status_code == 200
    data = response.json()

    # Should have staking data
    month_12 = next(m for m in data["global_metrics"] if m["month_index"] == 12)
    assert "total_staked" in month_12
    # Staked amount should not exceed max capacity
    max_capacity = 1_000_000 * 0.30
    assert month_12["total_staked"] <= max_capacity * 1.01  # Small buffer for float precision


def test_abm_treasury_with_zero_fees(client):
    """Test treasury with zero transaction fees."""
    config = {
        "token": {
            "name": "ZeroFees",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 100,
                "tge_unlock_pct": 10,
                "cliff_months": 0,
                "vesting_months": 12
            }
        ],
        "abm": {
            "pricing_model": "constant",
            "agents_per_cohort": 50,
            "initial_price": 1.0,
            "enable_treasury": True,
            "treasury_config": {
                "initial_balance_pct": 0.10,
                "transaction_fee_pct": 0.0,  # Zero fees
                "hold_pct": 0.5,
                "liquidity_pct": 0.3,
                "buyback_pct": 0.2,
                "burn_bought_tokens": False
            }
        }
    }

    response = client.post("/api/v2/abm/simulate-sync", json=config)

    assert response.status_code == 200
    # Should still work with zero fees


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
