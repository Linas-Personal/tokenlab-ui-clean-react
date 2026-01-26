"""
ABM Simulation API Routes.

Phase 1: Synchronous simulation endpoint (for quick sims)
Phase 2: Async job queue, SSE streaming, result caching
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
import logging

from app.models.abm_request import ABMSimulationRequest, ABMValidateRequest
from app.models.abm_response import (
    ABMSimulationResults, ABMGlobalMetric, ABMSummaryCards, ABMCohortMetric,
    JobSubmissionResponse, JobStatusResponse, JobStatus
)
from app.abm.engine.simulation_loop import ABMSimulationLoop

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/abm", tags=["abm"])


@router.post("/simulate-sync", response_model=ABMSimulationResults)
async def run_abm_simulation_sync(request: ABMSimulationRequest):
    """
    Run ABM simulation (Phase 1: Synchronous).

    This is a simplified MVP endpoint that runs the simulation synchronously.
    Phase 2 will add async job queue for long-running simulations.

    Args:
        request: ABM simulation configuration

    Returns:
        ABM simulation results

    Raises:
        HTTPException: If simulation fails
    """
    try:
        logger.info(
            f"ABM simulation request: "
            f"{len(request.buckets)} cohorts, "
            f"{request.token.get('horizon_months', 12)} months, "
            f"pricing={request.abm.pricing_model}"
        )

        # Convert request to config dict (for ABMSimulationLoop.from_config)
        config = {
            "token": request.token,
            "buckets": request.buckets,
            "abm": request.abm.model_dump()
        }

        # Create simulation loop from config
        simulation_loop = ABMSimulationLoop.from_config(config)

        # Run simulation
        horizon_months = request.token.get("horizon_months", 12)
        results = await simulation_loop.run_full_simulation(months=horizon_months)

        # Convert to API response format
        api_response = _convert_to_api_response(results, simulation_loop)

        logger.info(
            f"ABM simulation completed: "
            f"{len(results.global_metrics)} months, "
            f"{api_response.execution_time_seconds:.2f}s"
        )

        return api_response

    except Exception as e:
        logger.error(f"ABM simulation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "simulation_error",
                "message": str(e)
            }
        )


@router.post("/simulate", response_model=JobSubmissionResponse)
async def submit_abm_simulation(request_obj: Request, config: ABMSimulationRequest):
    """
    Submit ABM simulation job (async, Phase 2).

    Returns immediately with job_id. Use /jobs/{job_id}/status to poll
    or /jobs/{job_id}/stream for real-time progress.

    Args:
        request_obj: FastAPI request object
        config: ABM simulation configuration

    Returns:
        Job submission response with job_id and URLs

    Raises:
        HTTPException: If job submission fails
    """
    try:
        # Get job queue from app state
        if not hasattr(request_obj.app.state, "abm_job_queue"):
            raise HTTPException(
                status_code=503,
                detail="Job queue not initialized. Using /simulate-sync instead."
            )

        job_queue = request_obj.app.state.abm_job_queue

        # Convert to config dict
        config_dict = {
            "token": config.token,
            "buckets": config.buckets,
            "abm": config.abm.model_dump()
        }

        # Submit job
        job_id = await job_queue.submit_job(config_dict)

        # Check if cached
        job_status = job_queue.get_job_status(job_id)
        is_cached = job_id.startswith("cached_")

        logger.info(
            f"ABM job submitted: {job_id} "
            f"(cached={is_cached}, config_hash={job_queue._compute_config_hash(config_dict)})"
        )

        return JobSubmissionResponse(
            job_id=job_id,
            status=JobStatus(job_status["status"]),
            status_url=f"/api/v2/abm/jobs/{job_id}/status",
            stream_url=f"/api/v2/abm/jobs/{job_id}/stream",
            cached=is_cached
        )

    except RuntimeError as e:
        # Too many concurrent jobs
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.error(f"Job submission failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error_type": "submission_error", "message": str(e)}
        )


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(request_obj: Request, job_id: str):
    """
    Get status of a submitted job.

    Args:
        request_obj: FastAPI request object
        job_id: Job ID

    Returns:
        Job status response

    Raises:
        HTTPException: If job not found
    """
    try:
        if not hasattr(request_obj.app.state, "abm_job_queue"):
            raise HTTPException(status_code=503, detail="Job queue not initialized")

        job_queue = request_obj.app.state.abm_job_queue
        job_status = job_queue.get_job_status(job_id)

        if job_status is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return JobStatusResponse(
            job_id=job_id,
            status=JobStatus(job_status["status"]),
            progress_pct=job_status["progress_pct"],
            current_month=job_status["current_month"],
            total_months=job_status["total_months"],
            error=job_status.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/results", response_model=ABMSimulationResults)
async def get_job_results(request_obj: Request, job_id: str):
    """
    Get results of a completed job.

    Args:
        request_obj: FastAPI request object
        job_id: Job ID

    Returns:
        Simulation results

    Raises:
        HTTPException: If job not found or not completed
    """
    try:
        if not hasattr(request_obj.app.state, "abm_job_queue"):
            raise HTTPException(status_code=503, detail="Job queue not initialized")

        job_queue = request_obj.app.state.abm_job_queue

        # Check job status
        job_status = job_queue.get_job_status(job_id)
        if job_status is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        if job_status["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Job not completed yet. Status: {job_status['status']}"
            )

        # Get results
        results = job_queue.get_job_results(job_id)
        if results is None:
            raise HTTPException(status_code=404, detail="Results not available")

        # Convert to API response format
        # Need to create a mock simulation_loop to use _convert_to_api_response
        # For now, we'll create a simplified response
        global_metrics = [
            ABMGlobalMetric(
                month_index=r.month_index,
                date=r.date,
                price=r.price,
                circulating_supply=r.circulating_supply,
                total_unlocked=r.total_unlocked,
                total_sold=r.total_sold,
                total_staked=r.total_staked,
                total_held=r.total_held
            )
            for r in results.global_metrics
        ]

        summary = _calculate_summary(global_metrics)

        return ABMSimulationResults(
            global_metrics=global_metrics,
            cohort_metrics=None,
            agent_snapshots=None,
            summary=summary,
            execution_time_seconds=results.execution_time_seconds,
            num_agents=results.config.get("num_agents", 0),
            num_cohorts=0,
            warnings=results.warnings
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/stream")
async def stream_job_progress(request_obj: Request, job_id: str):
    """
    Stream real-time progress updates via Server-Sent Events (SSE).

    Args:
        request_obj: FastAPI request object
        job_id: Job ID

    Returns:
        SSE stream
    """
    try:
        if not hasattr(request_obj.app.state, "abm_progress_streamer"):
            raise HTTPException(status_code=503, detail="Progress streaming not available")

        progress_streamer = request_obj.app.state.abm_progress_streamer

        return StreamingResponse(
            progress_streamer.stream_job_progress(job_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )

    except Exception as e:
        logger.error(f"Failed to start progress stream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def cancel_job(request_obj: Request, job_id: str):
    """
    Cancel a running job.

    Args:
        request_obj: FastAPI request object
        job_id: Job ID

    Returns:
        Success message

    Raises:
        HTTPException: If cancellation fails
    """
    try:
        if not hasattr(request_obj.app.state, "abm_job_queue"):
            raise HTTPException(status_code=503, detail="Job queue not initialized")

        job_queue = request_obj.app.state.abm_job_queue
        success = await job_queue.cancel_job(job_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Job {job_id} not found or not cancellable"
            )

        return JSONResponse(content={"message": f"Job {job_id} cancelled"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_jobs(request_obj: Request):
    """
    List all jobs (for monitoring/admin).

    Args:
        request_obj: FastAPI request object

    Returns:
        List of job statuses
    """
    try:
        if not hasattr(request_obj.app.state, "abm_job_queue"):
            raise HTTPException(status_code=503, detail="Job queue not initialized")

        job_queue = request_obj.app.state.abm_job_queue
        jobs = job_queue.get_all_jobs()

        return JSONResponse(content={"jobs": jobs})

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/stats")
async def get_queue_stats(request_obj: Request):
    """
    Get queue statistics.

    Args:
        request_obj: FastAPI request object

    Returns:
        Queue statistics
    """
    try:
        if not hasattr(request_obj.app.state, "abm_job_queue"):
            raise HTTPException(status_code=503, detail="Job queue not initialized")

        job_queue = request_obj.app.state.abm_job_queue
        stats = job_queue.get_stats()

        return JSONResponse(content=stats)

    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_abm_config(request: ABMValidateRequest):
    """
    Validate ABM configuration without running simulation.

    Args:
        request: Configuration to validate

    Returns:
        Validation result with warnings/errors
    """
    try:
        warnings = []
        errors = []

        # Basic validation
        token = request.config.token
        buckets = request.config.buckets

        # Check total allocation
        total_allocation = sum(b.get("allocation", 0) for b in buckets)
        if total_allocation > 100.01:
            errors.append(f"Total allocation ({total_allocation}%) exceeds 100%")

        # Check agent count doesn't exceed reasonable limits
        agents_per_cohort = request.config.abm.agents_per_cohort
        num_cohorts = len(buckets)
        total_agents = agents_per_cohort * num_cohorts

        if total_agents > 1000:
            warnings.append(
                f"High agent count ({total_agents}) may be slow. "
                f"Consider using meta_agents granularity."
            )

        # Check horizon
        horizon = token.get("horizon_months", 12)
        if horizon > 120:
            warnings.append(f"Very long horizon ({horizon} months) may be slow.")

        is_valid = len(errors) == 0

        return JSONResponse(content={
            "valid": is_valid,
            "warnings": warnings,
            "errors": errors
        })

    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=400,
            content={
                "valid": False,
                "warnings": [],
                "errors": [str(e)]
            }
        )


@router.post("/monte-carlo/simulate", response_model=JobSubmissionResponse)
async def submit_monte_carlo_simulation(request_obj: Request, config: ABMSimulationRequest):
    """
    Submit Monte Carlo simulation job (Phase 6).

    Runs multiple ABM simulation trials with different random seeds in parallel.
    Returns percentiles (P10, P50, P90) and confidence bands.

    Args:
        request_obj: FastAPI request object
        config: ABM simulation configuration with monte_carlo settings

    Returns:
        Job submission response with job_id and URLs

    Raises:
        HTTPException: If job submission fails or monte_carlo config missing
    """
    try:
        if not hasattr(request_obj.app.state, "abm_job_queue"):
            raise HTTPException(status_code=503, detail="Job queue not initialized")

        if not config.monte_carlo:
            raise HTTPException(
                status_code=400,
                detail="Monte Carlo configuration is required. Please provide monte_carlo settings."
            )

        job_queue = request_obj.app.state.abm_job_queue

        # Submit Monte Carlo job
        job_id = await job_queue.submit_monte_carlo_job(config.model_dump())

        logger.info(
            f"Monte Carlo simulation submitted: job_id={job_id}, "
            f"trials={config.monte_carlo.num_trials}"
        )

        return JobSubmissionResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            status_url=f"/api/v2/abm/jobs/{job_id}/status",
            stream_url=f"/api/v2/abm/jobs/{job_id}/stream",
            results_url=f"/api/v2/abm/monte-carlo/results/{job_id}",
            cached=False
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Monte Carlo job submission failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monte-carlo/results/{job_id}")
async def get_monte_carlo_results(request_obj: Request, job_id: str):
    """
    Get Monte Carlo simulation results.

    Returns trials, percentiles (P10, P50, P90), mean trajectory, and summary stats.

    Args:
        request_obj: FastAPI request object
        job_id: Job ID

    Returns:
        Monte Carlo results with percentiles and confidence bands

    Raises:
        HTTPException: If job not found or not completed
    """
    try:
        if not hasattr(request_obj.app.state, "abm_job_queue"):
            raise HTTPException(status_code=503, detail="Job queue not initialized")

        job_queue = request_obj.app.state.abm_job_queue

        # Check job status
        job_status = job_queue.get_job_status(job_id)
        if job_status is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        if job_status["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Monte Carlo simulation not completed yet. Status: {job_status['status']}"
            )

        # Get Monte Carlo results
        mc_results = job_queue.get_monte_carlo_results(job_id)
        if mc_results is None:
            raise HTTPException(
                status_code=404,
                detail="Monte Carlo results not available. Job may not be a Monte Carlo simulation."
            )

        return JSONResponse(content={
            "trials": [
                {
                    "trial_index": t.trial_index,
                    "global_metrics": t.global_metrics,
                    "final_price": t.final_price,
                    "total_sold": t.total_sold,
                    "seed": t.seed
                }
                for t in mc_results.trials
            ],
            "percentiles": [
                {
                    "percentile": p.percentile,
                    "global_metrics": p.global_metrics,
                    "final_price": p.final_price,
                    "total_sold": p.total_sold
                }
                for p in mc_results.percentiles
            ],
            "mean_metrics": mc_results.mean_metrics,
            "summary": mc_results.summary,
            "execution_time_seconds": mc_results.execution_time_seconds
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Monte Carlo results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _convert_to_api_response(
    results: "SimulationResults",
    simulation_loop: ABMSimulationLoop
) -> ABMSimulationResults:
    """
    Convert internal SimulationResults to API response format.

    Args:
        results: Internal simulation results
        simulation_loop: Simulation loop instance

    Returns:
        ABMSimulationResults for API
    """
    # Convert global metrics
    global_metrics = [
        ABMGlobalMetric(
            month_index=r.month_index,
            date=r.date,
            price=r.price,
            circulating_supply=r.circulating_supply,
            total_unlocked=r.total_unlocked,
            total_sold=r.total_sold,
            total_staked=r.total_staked,
            total_held=r.total_held
        )
        for r in results.global_metrics
    ]

    # Convert cohort metrics (if stored)
    cohort_metrics = None
    if results.global_metrics and results.global_metrics[0].cohort_results:
        cohort_metrics = []
        for r in results.global_metrics:
            if r.cohort_results:
                for cohort_name, cohort_data in r.cohort_results.items():
                    cohort_metrics.append(ABMCohortMetric(
                        month_index=r.month_index,
                        cohort_name=cohort_name,
                        total_sold=cohort_data["total_sell"],
                        total_staked=cohort_data["total_stake"],
                        total_held=cohort_data["total_hold"],
                        num_agents=cohort_data["num_agents"]
                    ))

    # Calculate summary statistics
    summary = _calculate_summary(global_metrics)

    # Count unique cohorts
    cohorts_set = set()
    for agent in simulation_loop.agents:
        cohorts_set.add(agent.attrs.cohort)

    return ABMSimulationResults(
        global_metrics=global_metrics,
        cohort_metrics=cohort_metrics,
        agent_snapshots=None,  # Not included in Phase 1
        summary=summary,
        execution_time_seconds=results.execution_time_seconds,
        num_agents=len(simulation_loop.agents),
        num_cohorts=len(cohorts_set),
        warnings=results.warnings
    )


def _calculate_summary(metrics: list[ABMGlobalMetric]) -> ABMSummaryCards:
    """
    Calculate summary statistics from global metrics.

    Args:
        metrics: List of global metrics

    Returns:
        Summary cards
    """
    if not metrics:
        return ABMSummaryCards(
            max_sell_month=0,
            max_sell_tokens=0.0,
            final_price=0.0,
            final_circulating_supply=0.0,
            total_tokens_sold=0.0,
            average_price=0.0
        )

    # Find max sell month
    max_sell_month = max(metrics, key=lambda m: m.total_sold).month_index
    max_sell_tokens = max(m.total_sold for m in metrics)

    # Final values
    final_metric = metrics[-1]
    final_price = final_metric.price
    final_circulating_supply = final_metric.circulating_supply

    # Total sold (cumulative)
    total_tokens_sold = sum(m.total_sold for m in metrics)

    # Average price (weighted by sell volume)
    total_sell_value = sum(m.total_sold * m.price for m in metrics)
    average_price = total_sell_value / total_tokens_sold if total_tokens_sold > 0 else 0.0

    return ABMSummaryCards(
        max_sell_month=max_sell_month,
        max_sell_tokens=max_sell_tokens,
        final_price=final_price,
        final_circulating_supply=final_circulating_supply,
        total_tokens_sold=total_tokens_sold,
        average_price=average_price
    )
