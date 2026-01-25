"""
FastAPI application main entry point.
"""
import logging
import sys
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api.routes import simulation, health
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
# Use env var to disable rate limiting in tests
rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/minute"] if not rate_limit_enabled else ["100/minute"],
    enabled=rate_limit_enabled
)

app = FastAPI(
    title="Vesting Simulator API",
    description="REST API for TokenLab vesting simulation engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
# Can be configured via environment variable CORS_ORIGINS (comma-separated list)
# Default to common dev ports if not specified
cors_origins_str = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:5174,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:3000"
)
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS configured for origins: {cors_origins}")

# Request size limit middleware
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", "10485760"))  # 10MB default

@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Limit request body size to prevent memory exhaustion."""
    content_length = request.headers.get("content-length")
    if content_length:
        content_length = int(content_length)
        if content_length > MAX_REQUEST_SIZE:
            logger.warning(f"Request too large: {content_length} bytes (max: {MAX_REQUEST_SIZE})")
            return JSONResponse(
                status_code=413,
                content={
                    "status": "error",
                    "error_type": "request_too_large",
                    "message": f"Request body too large. Maximum allowed size is {MAX_REQUEST_SIZE} bytes."
                }
            )

    response = await call_next(request)
    return response

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing."""
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"Status={response.status_code} Time={process_time:.3f}s"
    )

    return response

# Register routers
app.include_router(simulation.router)
app.include_router(health.router)

logger.info("Vesting Simulator API initialized")


@app.get("/")
async def root():
    """Root endpoint."""
    return JSONResponse(
        content={
            "message": "Vesting Simulator API",
            "version": "1.0.0",
            "docs": "/docs"
        }
    )


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Vesting Simulator API server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
