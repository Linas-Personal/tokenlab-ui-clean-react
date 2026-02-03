"""Pytest configuration and fixtures for test suite."""

import os
os.environ["RATE_LIMIT_ENABLED"] = "true"

import pytest
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient
from app.main import app
from app.abm.async_engine.job_queue import AsyncJobQueue
from app.abm.async_engine.progress_streaming import ProgressStreamer


# Configure pytest-anyio to only use asyncio backend
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@asynccontextmanager
async def test_lifespan(app):
    """Lifespan context manager for tests - initializes job queue."""
    app.state.abm_job_queue = AsyncJobQueue(max_concurrent_jobs=5, job_ttl_hours=24)
    app.state.abm_job_queue.start_cleanup_task()
    app.state.abm_progress_streamer = ProgressStreamer(app.state.abm_job_queue)

    yield

    await app.state.abm_job_queue.shutdown()


# Override app lifespan for tests
app.router.lifespan_context = test_lifespan


@pytest.fixture(scope="function")
def test_client():
    """Test client with lifespan support.

    Uses function scope to ensure each test gets a fresh client
    with clean middleware state (rate limiting, etc.).
    """
    # Reset rate limiter state before each test
    from app.main import limiter
    from app.api.routes.health import limiter as health_limiter
    from app.api.routes.simulation import limiter as simulation_limiter
    import random
    limiter.reset()
    health_limiter.reset()
    simulation_limiter.reset()

    # Create client with unique remote address to isolate rate limiting per test
    with TestClient(app, base_url=f"http://test-{random.randint(1000000, 9999999)}.example.com") as client:
        yield client

    # Clean up rate limiter state after test
    limiter.reset()
    health_limiter.reset()
    simulation_limiter.reset()
