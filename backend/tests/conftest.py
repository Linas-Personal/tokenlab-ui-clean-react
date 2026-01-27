"""Pytest configuration and fixtures for test suite."""

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


@pytest.fixture(scope="module")
def test_client():
    """Test client with lifespan support."""
    with TestClient(app) as client:
        yield client
