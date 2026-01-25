"""
Simulation API routes.
"""
import logging
from fastapi import APIRouter, HTTPException, Request
from typing import Any
import time
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.request import SimulateRequest, ValidateConfigRequest
from app.models.response import SimulateResponse, ValidationResponse, ErrorResponse
from app.services.simulator_service import SimulatorService

router = APIRouter(prefix="/api/v1", tags=["simulation"])
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)


# OPTIONS endpoints for CORS preflight requests
@router.options("/simulate")
async def simulate_options():
    """Handle CORS preflight for simulate endpoint."""
    return {"detail": "OK"}


@router.options("/config/validate")
async def validate_options():
    """Handle CORS preflight for validate endpoint."""
    return {"detail": "OK"}


@router.post("/simulate", response_model=SimulateResponse)
@limiter.limit("20/minute")  # 20 per minute = allows reasonable testing while preventing abuse
def simulate(request: Request, sim_request: SimulateRequest) -> SimulateResponse:
    """
    Run vesting simulation.

    Args:
        request: Simulation request with configuration

    Returns:
        Simulation results with warnings

    Raises:
        HTTPException: If simulation fails
    """
    start_time = time.time()
    logger.info(f"Starting simulation: mode={sim_request.config.token.simulation_mode}, "
                f"horizon={sim_request.config.token.horizon_months} months")

    try:
        simulation_data, warnings = SimulatorService.run_simulation(sim_request.config)

        execution_time_ms = (time.time() - start_time) * 1000
        logger.info(f"Simulation completed successfully in {execution_time_ms:.2f}ms, "
                   f"warnings={len(warnings)}")

        return SimulateResponse(
            status="success",
            execution_time_ms=round(execution_time_ms, 2),
            warnings=warnings,
            data=simulation_data
        )

    except ValueError as e:
        logger.warning(f"Validation error in simulation: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail={
                "status": "error",
                "error_type": "validation_error",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Simulation failed with exception: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_type": "simulation_error",
                "message": f"Simulation failed: {str(e)}"
            }
        )


@router.post("/config/validate", response_model=ValidationResponse)
@limiter.limit("30/minute")
def validate_config(request: Request, config_request: ValidateConfigRequest) -> ValidationResponse:
    """
    Validate configuration without running simulation.

    Args:
        request: Configuration to validate

    Returns:
        Validation results with warnings and errors
    """
    logger.info("Config validation requested")
    is_valid, warnings, errors = SimulatorService.validate_config_dict(config_request.config)

    if is_valid:
        logger.info(f"Config valid with {len(warnings)} warnings")
    else:
        logger.warning(f"Config invalid with {len(errors)} errors")

    return ValidationResponse(
        valid=is_valid,
        warnings=warnings,
        errors=errors
    )
