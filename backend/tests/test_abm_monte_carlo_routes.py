"""
Integration tests for ABM Monte Carlo API routes.

These tests hit real FastAPI endpoints with real dependencies and verify:
- Error handling for missing Monte Carlo config
- End-to-end Monte Carlo job submission and results
- Error response when querying Monte Carlo results for non-MC jobs
"""

import time

import pytest


@pytest.fixture
def client(test_client):
    """Use test_client fixture from conftest.py with function scope."""
    return test_client


def _base_abm_config():
    return {
        "token": {
            "name": "MC-Route-Test",
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
            "agents_per_cohort": 25,
            "initial_price": 1.0
        }
    }


def _wait_for_job_completion(client, job_id, max_polls=60, sleep_s=0.1):
    for _ in range(max_polls):
        status_response = client.get(f"/api/v2/abm/jobs/{job_id}/status")
        assert status_response.status_code == 200
        status_data = status_response.json()

        if status_data["status"] == "completed":
            return status_data

        time.sleep(sleep_s)

    raise AssertionError("Job did not complete within expected time")


def test_monte_carlo_requires_config(client):
    """Missing Monte Carlo config should return 400 with clear error message."""
    config = _base_abm_config()

    response = client.post("/api/v2/abm/monte-carlo/simulate", json=config)

    assert response.status_code == 400
    data = response.json()
    assert "monte carlo" in data["detail"].lower()


def test_monte_carlo_results_flow(client):
    """Submit Monte Carlo job and verify result payload contents."""
    config = _base_abm_config()
    config["monte_carlo"] = {
        "enabled": True,
        "num_trials": 10,
        "variance_level": "low",
        "confidence_levels": [10, 50, 90],
        "seed": 123
    }

    submit_response = client.post("/api/v2/abm/monte-carlo/simulate", json=config)

    assert submit_response.status_code == 200
    submit_data = submit_response.json()
    job_id = submit_data["job_id"]
    assert submit_data["status"] in ["pending", "running"]
    assert submit_data["results_url"].endswith(f"/api/v2/abm/monte-carlo/results/{job_id}")

    _wait_for_job_completion(client, job_id)

    results_response = client.get(f"/api/v2/abm/monte-carlo/results/{job_id}")

    assert results_response.status_code == 200
    results = results_response.json()

    assert len(results["trials"]) == 10
    assert len(results["percentiles"]) == 3
    assert len(results["mean_metrics"]) == config["token"]["horizon_months"]
    assert results["summary"]["num_trials"] == 10
    assert results["execution_time_seconds"] >= 0

    first_trial = results["trials"][0]
    assert first_trial["trial_index"] == 0
    assert len(first_trial["global_metrics"]) == config["token"]["horizon_months"]
    assert first_trial["global_metrics"][0]["month_index"] == 0
    assert first_trial["global_metrics"][-1]["month_index"] == config["token"]["horizon_months"] - 1
    assert first_trial["final_price"] > 0

    percentile_entry = results["percentiles"][0]
    assert percentile_entry["percentile"] in [10, 50, 90]
    assert len(percentile_entry["global_metrics"]) == config["token"]["horizon_months"]


def test_monte_carlo_results_for_non_mc_job(client):
    """Querying Monte Carlo results for a non-MC job should return 404."""
    config = _base_abm_config()

    submit_response = client.post("/api/v2/abm/simulate", json=config)

    assert submit_response.status_code == 200
    job_id = submit_response.json()["job_id"]

    _wait_for_job_completion(client, job_id)

    results_response = client.get(f"/api/v2/abm/monte-carlo/results/{job_id}")

    assert results_response.status_code == 404
    data = results_response.json()
    assert "monte carlo" in data["detail"].lower()
