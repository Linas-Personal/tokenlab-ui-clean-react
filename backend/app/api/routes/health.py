"""
Health check API routes.
"""
import logging
import time
import psutil
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models.response import HealthResponse

router = APIRouter(prefix="/api/v1", tags=["health"])
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

# Track uptime
_start_time = time.time()


@router.get("/health/live")
def liveness_probe():
    """Kubernetes liveness probe - returns 200 if process is alive."""
    return {"status": "alive"}


@router.get("/health/ready")
def readiness_probe(request: Request):
    """Kubernetes readiness probe - returns 200 if ready to serve traffic."""
    checks = {
        "job_queue": hasattr(request.app.state, "abm_job_queue"),
        "progress_streamer": hasattr(request.app.state, "abm_progress_streamer")
    }

    all_ready = all(checks.values())

    if not all_ready:
        logger.warning(f"Readiness check failed: {checks}")
        return {"status": "not_ready", "checks": checks}, 503

    return {"status": "ready", "checks": checks}


@router.get("/health", response_model=HealthResponse)
@limiter.limit("60/minute")
def health_check(request: Request) -> HealthResponse:
    uptime_seconds = int(time.time() - _start_time)
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()

    logger.debug(f"Health check: uptime={uptime_seconds}s, cpu={cpu_percent}%, "
                 f"memory={memory.percent}%")

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=uptime_seconds,
        cpu_percent=cpu_percent,
        memory_percent=memory.percent
    )
