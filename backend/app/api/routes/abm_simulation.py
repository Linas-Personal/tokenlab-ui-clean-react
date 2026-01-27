"""ABM Simulation API Routes."""
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, StreamingResponse
import logging

from app.models.abm_request import ABMSimulationRequest, ABMValidateRequest
from app.models.abm_response import (
    ABMSimulationResults, ABMGlobalMetric, ABMSummaryCards, ABMCohortMetric,
    JobSubmissionResponse, JobStatusResponse, JobStatus
)
from app.abm.engine.simulation_loop import ABMSimulationLoop
from app.utils.config_migration import migrate_legacy_config, validate_migrated_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/abm", tags=["abm"])


def get_job_queue(request: Request):
    if not hasattr(request.app.state, "abm_job_queue"):
        raise HTTPException(status_code=503, detail="Job queue not initialized")
    return request.app.state.abm_job_queue


def get_progress_streamer(request: Request):
    if not hasattr(request.app.state, "abm_progress_streamer"):
        raise HTTPException(status_code=503, detail="Progress streaming not available")
    return request.app.state.abm_progress_streamer


@router.post("/simulate-sync", response_model=ABMSimulationResults)
async def run_abm_simulation_sync(request: ABMSimulationRequest):
    try:
        logger.info(
            f"ABM simulation request: "
            f"{len(request.buckets)} cohorts, "
            f"{request.token.horizon_months} months, "
            f"pricing={request.abm.pricing_model}"
        )

        config = {
            "token": request.token.model_dump(),
            "buckets": [bucket.model_dump() for bucket in request.buckets],
            "abm": request.abm.model_dump()
        }

        migration_warnings = []
        simulation_mode = config.get("token", {}).get("simulation_mode", "abm")
        if simulation_mode in ["tier1", "tier2", "tier3"]:
            logger.info(f"Migrating legacy config: {simulation_mode} -> abm")
            config, migration_warnings = migrate_legacy_config(config)
            recommendations = validate_migrated_config(config)

            for warning in migration_warnings:
                logger.warning(f"Config migration: {warning}")
            for rec in recommendations:
                logger.info(f"Config recommendation: {rec}")

            migration_warnings.extend(recommendations)

        simulation_loop = ABMSimulationLoop.from_config(config)

        horizon_months = request.token.horizon_months
        results = await simulation_loop.run_full_simulation(months=horizon_months)

        results.warnings.extend(migration_warnings)

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
async def submit_abm_simulation(
    config: ABMSimulationRequest,
    job_queue = Depends(get_job_queue)
):
    try:
        config_dict = {
            "token": config.token.model_dump(),
            "buckets": [bucket.model_dump() for bucket in config.buckets],
            "abm": config.abm.model_dump()
        }

        simulation_mode = config_dict.get("token", {}).get("simulation_mode", "abm")
        if simulation_mode in ["tier1", "tier2", "tier3"]:
            logger.info(f"Migrating legacy config for async job: {simulation_mode} -> abm")
            config_dict, migration_warnings = migrate_legacy_config(config_dict)
            recommendations = validate_migrated_config(config_dict)

            for warning in migration_warnings:
                logger.warning(f"Config migration (async): {warning}")
            for rec in recommendations:
                logger.info(f"Config recommendation (async): {rec}")

            if "_migration_warnings" not in config_dict:
                config_dict["_migration_warnings"] = []
            config_dict["_migration_warnings"].extend(migration_warnings)
            config_dict["_migration_warnings"].extend(recommendations)

        job_id = await job_queue.submit_job(config_dict)

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
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.error(f"Job submission failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error_type": "submission_error", "message": str(e)}
        )


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str, job_queue = Depends(get_job_queue)):
    try:
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
async def get_job_results(job_id: str, job_queue = Depends(get_job_queue)):
    try:
        job_status = job_queue.get_job_status(job_id)
        if job_status is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        if job_status["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Job not completed yet. Status: {job_status['status']}"
            )

        results = job_queue.get_job_results(job_id)
        if results is None:
            raise HTTPException(status_code=404, detail="Results not available")
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
async def stream_job_progress(
    job_id: str,
    progress_streamer = Depends(get_progress_streamer)
):
    try:
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
async def cancel_job(job_id: str, job_queue = Depends(get_job_queue)):
    try:
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
async def list_jobs(job_queue = Depends(get_job_queue)):
    try:
        jobs = job_queue.get_all_jobs()

        return JSONResponse(content={"jobs": jobs})

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/stats")
async def get_queue_stats(job_queue = Depends(get_job_queue)):
    try:
        stats = job_queue.get_stats()

        return JSONResponse(content=stats)

    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_abm_config(request: ABMValidateRequest):
    try:
        warnings = []
        errors = []

        token = request.config.token
        buckets = request.config.buckets

        total_allocation = sum(b.get("allocation", 0) for b in buckets)
        if total_allocation > 100.01:
            errors.append(f"Total allocation ({total_allocation}%) exceeds 100%")

        agents_per_cohort = request.config.abm.agents_per_cohort
        num_cohorts = len(buckets)
        total_agents = agents_per_cohort * num_cohorts

        if total_agents > 1000:
            warnings.append(
                f"High agent count ({total_agents}) may be slow. "
                f"Consider using meta_agents granularity."
            )

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
async def submit_monte_carlo_simulation(
    config: ABMSimulationRequest,
    job_queue = Depends(get_job_queue)
):
    try:
        if not config.monte_carlo:
            raise HTTPException(
                status_code=400,
                detail="Monte Carlo configuration is required. Please provide monte_carlo settings."
            )

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
async def get_monte_carlo_results(job_id: str, job_queue = Depends(get_job_queue)):
    try:
        job_status = job_queue.get_job_status(job_id)
        if job_status is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        if job_status["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Monte Carlo simulation not completed yet. Status: {job_status['status']}"
            )

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

    summary = _calculate_summary(global_metrics)

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
    if not metrics:
        return ABMSummaryCards(
            max_sell_month=0, max_sell_tokens=0.0, final_price=0.0,
            final_circulating_supply=0.0, total_tokens_sold=0.0, average_price=0.0
        )

    max_sell_month = max(metrics, key=lambda m: m.total_sold)

    total_tokens_sold = sum(m.total_sold for m in metrics)
    total_sell_value = sum(m.total_sold * m.price for m in metrics)

    final = metrics[-1]

    return ABMSummaryCards(
        max_sell_month=max_sell_month.month_index,
        max_sell_tokens=max_sell_month.total_sold,
        final_price=final.price,
        final_circulating_supply=final.circulating_supply,
        total_tokens_sold=total_tokens_sold,
        average_price=total_sell_value / total_tokens_sold if total_tokens_sold > 0 else 0.0
    )
