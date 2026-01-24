"""
Simulation API routes.
"""
from fastapi import APIRouter, HTTPException
from typing import Any
import time

from app.models.request import SimulateRequest, ValidateConfigRequest
from app.models.response import SimulateResponse, ValidationResponse, ErrorResponse
from app.services.simulator_service import SimulatorService

router = APIRouter(prefix="/api/v1", tags=["simulation"])


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(request: SimulateRequest) -> SimulateResponse:
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

    try:
        simulation_data, warnings = SimulatorService.run_simulation(request.config)

        execution_time_ms = (time.time() - start_time) * 1000

        return SimulateResponse(
            status="success",
            execution_time_ms=round(execution_time_ms, 2),
            warnings=warnings,
            data=simulation_data
        )

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "status": "error",
                "error_type": "validation_error",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_type": "simulation_error",
                "message": f"Simulation failed: {str(e)}"
            }
        )


@router.post("/config/validate", response_model=ValidationResponse)
async def validate_config(request: ValidateConfigRequest) -> ValidationResponse:
    """
    Validate configuration without running simulation.

    Args:
        request: Configuration to validate

    Returns:
        Validation results with warnings and errors
    """
    is_valid, warnings, errors = SimulatorService.validate_config_dict(request.config)

    return ValidationResponse(
        valid=is_valid,
        warnings=warnings,
        errors=errors
    )
