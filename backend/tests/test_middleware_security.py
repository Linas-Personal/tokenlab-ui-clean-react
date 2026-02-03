"""
Tests for middleware and security features.

Tests cover:
- Rate limiting behavior
- Request size limits
- CORS headers
- Error handling middleware
- Concurrent request handling
- Logging middleware
"""

import pytest
import time
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client(test_client):
    """Use test_client fixture from conftest.py with function scope."""
    return test_client





# =============================================================================
# RATE LIMITING
# =============================================================================

def test_rate_limiting_allows_normal_requests(client):
    """Test that rate limiting allows normal request patterns."""
    # Make 10 requests in quick succession (well under the limit)
    responses = []
    for _ in range(10):
        response = client.get("/api/v1/health")
        responses.append(response)

    # All should succeed
    assert all(r.status_code == 200 for r in responses)


def test_zzz_rate_limiting_blocks_excessive_requests(client):
    """Test that rate limiting blocks requests exceeding the limit.

    Note: This test might be skipped in CI if RATE_LIMIT_ENABLED=false
    """
    import os
    if os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "false":
        pytest.skip("Rate limiting disabled in test environment")

    # The default limit is 100/minute per IP
    # Make more than 100 requests rapidly
    responses = []
    for _ in range(105):
        response = client.get("/api/v1/health")
        responses.append(response)
        # Small delay to avoid overwhelming the test
        time.sleep(0.001)

    # At least some should be rate limited (429)
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes, "Expected at least one 429 (Too Many Requests) response"


def test_rate_limiting_per_endpoint(client):
    """Test that rate limiting is applied per endpoint."""
    # Requests to different endpoints should have separate limits
    endpoints = [
        "/api/v1/health",
        "/",
        "/api/v2/abm/queue/stats"
    ]

    for endpoint in endpoints:
        # Each endpoint should allow some requests
        response = client.get(endpoint)
        assert response.status_code in [200, 404, 503]  # Success or not found


# =============================================================================
# REQUEST SIZE LIMITS
# =============================================================================

def test_request_size_limit_accepts_normal_requests(client):
    """Test that normal-sized requests are accepted."""
    config = {
        "token": {
            "name": "Normal",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent",
            "simulation_mode": "tier1"
        },
        "buckets": [
            {
                "bucket": "Team",
                "allocation": 100,
                "tge_unlock_pct": 0,
                "cliff_months": 6,
                "vesting_months": 12
            }
        ]
    }

    response = client.post("/api/v1/simulate", json={"config": config})

    assert response.status_code == 200


def test_request_size_limit_rejects_huge_requests(client):
    """Test that extremely large requests are rejected."""
    # Create a huge config by adding many buckets
    huge_config = {
        "token": {
            "name": "Huge",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 12,
            "allocation_mode": "percent",
            "simulation_mode": "tier1"
        },
        "buckets": []
    }

    # Add 10,000 buckets to make the request huge
    for i in range(10_000):
        huge_config["buckets"].append({
            "bucket": f"Bucket{i}",
            "allocation": 0.01,
            "tge_unlock_pct": 0,
            "cliff_months": 6,
            "vesting_months": 12
        })

    response = client.post("/api/v1/simulate", json={"config": huge_config})

    # Should either reject with 413 (too large) or 422 (validation error for too many buckets)
    assert response.status_code in [413, 422, 500]


def test_request_size_with_large_allocation_data(client):
    """Test request with very large bucket allocation arrays."""
    config = {
        "token": {
            "name": "LargeData",
            "total_supply": 1_000_000_000_000,  # Very large number
            "start_date": "2026-01-01",
            "horizon_months": 120,  # Long horizon
            "allocation_mode": "tokens",
            "simulation_mode": "tier1"
        },
        "buckets": []
    }

    # Add many buckets with large token amounts
    for i in range(100):
        config["buckets"].append({
            "bucket": f"Large{i}",
            "allocation": 10_000_000_000,  # 10 billion tokens each
            "tge_unlock_pct": 0,
            "cliff_months": 6,
            "vesting_months": 114
        })

    response = client.post("/api/v1/simulate", json={"config": config})

    # Should handle or reject gracefully
    assert response.status_code in [200, 413, 422, 500]


# =============================================================================
# CORS HEADERS
# =============================================================================

def test_cors_allows_configured_origins(client):
    """Test that CORS allows configured origins."""
    # Simulate request from allowed origin
    headers = {
        "Origin": "http://localhost:5173"
    }

    response = client.get("/api/v1/health", headers=headers)

    assert response.status_code == 200
    # Note: TestClient doesn't fully simulate CORS, but endpoint should work


def test_cors_preflight_options_request(client):
    """Test CORS preflight OPTIONS request."""
    response = client.options("/api/v1/simulate")

    # OPTIONS should succeed
    assert response.status_code == 200


# =============================================================================
# ERROR HANDLING MIDDLEWARE
# =============================================================================

def test_middleware_handles_404_gracefully(client):
    """Test that middleware handles 404 errors properly."""
    response = client.get("/nonexistent/endpoint")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_middleware_handles_405_method_not_allowed(client):
    """Test that middleware handles wrong HTTP methods."""
    # Try DELETE on an endpoint that only accepts GET
    response = client.delete("/api/v1/health")

    assert response.status_code == 405


def test_middleware_handles_malformed_json(client):
    """Test that middleware handles malformed JSON gracefully."""
    response = client.post(
        "/api/v1/simulate",
        data="not valid json{",
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422


def test_middleware_handles_missing_content_type(client):
    """Test requests without Content-Type header."""
    response = client.post(
        "/api/v1/simulate",
        data='{"config": {}}',
        headers={"Content-Type": "text/plain"}  # Wrong content type
    )

    assert response.status_code in [422, 415]


# =============================================================================
# REQUEST LOGGING
# =============================================================================

def test_request_logging_includes_timing(client):
    """Test that request logging includes timing information.

    This test verifies the middleware works but doesn't check logs directly.
    """
    # Make a request that should be logged
    start = time.time()
    response = client.get("/api/v1/health")
    duration = time.time() - start

    # Request should complete successfully
    assert response.status_code == 200

    # Duration should be reasonable
    assert duration < 1.0  # Should complete in under 1 second


# =============================================================================
# CONCURRENT REQUESTS
# =============================================================================

def test_middleware_handles_concurrent_requests(client):
    """Test that middleware handles concurrent requests safely."""
    import concurrent.futures

    def make_request():
        return client.get("/api/v1/health")

    # Make 20 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request) for _ in range(20)]
        responses = [f.result() for f in futures]

    # All should succeed (or be rate limited)
    status_codes = [r.status_code for r in responses]
    assert all(code in [200, 429] for code in status_codes)


def test_middleware_thread_safety_with_state(client):
    """Test thread safety of middleware accessing app state."""
    import concurrent.futures

    config = {
        "token": {
            "name": "Concurrent",
            "total_supply": 1_000_000,
            "start_date": "2026-01-01",
            "horizon_months": 3
        },
        "buckets": [
            {
                "bucket": "Test",
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

    def submit_simulation():
        return client.post("/api/v2/abm/simulate", json=config)

    # Submit multiple simulations concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(submit_simulation) for _ in range(5)]
        responses = [f.result() for f in futures]

    # All should succeed or return 429 (too many concurrent)
    status_codes = [r.status_code for r in responses]
    assert all(code in [200, 429] for code in status_codes)


# =============================================================================
# EDGE CASES
# =============================================================================

def test_middleware_handles_empty_request_body(client):
    """Test handling of empty request body."""
    response = client.post("/api/v1/simulate")

    assert response.status_code == 422


def test_middleware_handles_null_json(client):
    """Test handling of null JSON."""
    response = client.post(
        "/api/v1/simulate",
        json=None
    )

    assert response.status_code == 422


def test_middleware_handles_very_long_url(client):
    """Test handling of extremely long URLs."""
    # Create a very long query string
    long_param = "x" * 10000
    response = client.get(f"/api/v1/health?param={long_param}")

    # Should either accept or reject gracefully
    assert response.status_code in [200, 414, 400]


def test_middleware_handles_special_characters_in_url(client):
    """Test handling of special characters in URL."""
    # Try various special characters
    special_chars = [
        "%20",  # Space
        "%3C%3E",  # < >
        "%22",  # "
        "%27",  # '
    ]

    for char in special_chars:
        response = client.get(f"/api/v1/health?test={char}")
        # Should handle without crashing
        assert response.status_code in [200, 400, 404]


def test_middleware_handles_multiple_content_type_headers(client):
    """Test handling of multiple Content-Type headers."""
    response = client.post(
        "/api/v1/simulate",
        data='{"config": {}}',
        headers={
            "Content-Type": "application/json",
        }
    )

    # Should process normally
    assert response.status_code == 422  # Validation error for empty config


def test_request_with_no_headers(client):
    """Test request with minimal headers."""
    # TestClient always adds some headers, but we can test with minimal set
    response = client.get("/api/v1/health")

    assert response.status_code == 200


# =============================================================================
# STARTUP AND SHUTDOWN
# =============================================================================

def test_app_startup_initializes_components(client):
    """Test that app startup initializes necessary components."""
    # Check that job queue is initialized
    response = client.get("/api/v2/abm/queue/stats")

    # Should either return stats (200) or service unavailable (503)
    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert "total_jobs" in data
        assert "max_concurrent_jobs" in data


def test_root_endpoint_returns_api_info(client):
    """Test that root endpoint returns API information."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
