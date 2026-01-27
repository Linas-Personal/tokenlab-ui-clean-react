"""
Async Job Queue System.

Phase 2 MVP: In-memory job queue using asyncio (no Redis dependency).
Can be upgraded to Redis-backed in production if needed.
"""
import asyncio
import uuid
import time
import hashlib
import json
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta, timezone
from enum import Enum
import logging

from app.abm.engine.simulation_loop import ABMSimulationLoop, SimulationResults
from app.abm.monte_carlo.parallel_mc import MonteCarloEngine, MonteCarloResults

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobInfo:
    """Job metadata and state."""

    def __init__(self, job_id: str, config: Dict[str, Any]):
        self.job_id = job_id
        self.config = config
        self.status = JobStatus.PENDING
        self.created_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        # Progress tracking
        self.current_month: int = 0
        self.total_months: int = config.get("token", {}).get("horizon_months", 12)
        self.progress_pct: float = 0.0

        # Results
        self.results: Optional[SimulationResults] = None
        self.mc_results: Optional[MonteCarloResults] = None
        self.error: Optional[str] = None
        self.is_monte_carlo: bool = False

        # Task reference
        self.task: Optional[asyncio.Task] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "current_month": self.current_month,
            "total_months": self.total_months,
            "progress_pct": self.progress_pct,
            "error": self.error
        }


class AsyncJobQueue:
    """
    In-memory async job queue for ABM simulations.

    Features:
    - Async job submission
    - Progress tracking
    - Result caching by config hash
    - Automatic cleanup of old jobs
    """

    def __init__(self, max_concurrent_jobs: int = 5, job_ttl_hours: int = 24):
        """Initialize job queue with concurrency limits and TTL."""
        self.max_concurrent_jobs = max_concurrent_jobs
        self.job_ttl_hours = job_ttl_hours
        self.jobs: Dict[str, JobInfo] = {}
        self.result_cache: Dict[str, SimulationResults] = {}
        self.cache_ttl: Dict[str, datetime] = {}
        self.cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"AsyncJobQueue initialized: max_concurrent={max_concurrent_jobs}, ttl={job_ttl_hours}h")

    def start_cleanup_task(self):
        """Start background cleanup task."""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Cleanup task started")

    async def _cleanup_loop(self):
        """Background task to cleanup old jobs."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._cleanup_old_jobs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup task error: {e}", exc_info=True)

    async def _cleanup_old_jobs(self):
        """Remove old completed/failed jobs."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.job_ttl_hours)
        jobs_to_remove = [
            job_id for job_id, job_info in self.jobs.items()
            if job_info.status in {JobStatus.COMPLETED, JobStatus.FAILED}
            and job_info.completed_at and job_info.completed_at < cutoff
        ]

        for job_id in jobs_to_remove:
            del self.jobs[job_id]

        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")

    def _compute_config_hash(self, config: Dict[str, Any]) -> str:
        """Compute deterministic hash of configuration for caching."""
        config_json = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_json.encode()).hexdigest()[:16]

    async def submit_job(self, config: Dict[str, Any]) -> str:
        """
        Submit a new ABM simulation job.

        Args:
            config: Simulation configuration

        Returns:
            Job ID

        Raises:
            RuntimeError: If too many concurrent jobs
        """
        # Check cache first
        config_hash = self._compute_config_hash(config)
        if config_hash in self.result_cache:
            cache_age = datetime.now(timezone.utc) - self.cache_ttl[config_hash]
            if cache_age < timedelta(hours=2):
                logger.info(f"Cache hit for config_hash={config_hash}")

                # Create a completed job with cached results
                job_id = f"cached_{uuid.uuid4().hex[:12]}"
                job_info = JobInfo(job_id, config)
                job_info.status = JobStatus.COMPLETED
                job_info.started_at = datetime.now(timezone.utc)
                job_info.completed_at = datetime.now(timezone.utc)
                job_info.progress_pct = 100.0
                job_info.current_month = job_info.total_months
                job_info.results = self.result_cache[config_hash]
                self.jobs[job_id] = job_info

                return job_id

        # Check concurrent job limit
        running_jobs = sum(1 for j in self.jobs.values() if j.status == JobStatus.RUNNING)
        if running_jobs >= self.max_concurrent_jobs:
            raise RuntimeError(
                f"Maximum concurrent jobs ({self.max_concurrent_jobs}) reached. "
                f"Try again later."
            )

        # Create job
        job_id = f"abm_{uuid.uuid4().hex[:12]}"
        job_info = JobInfo(job_id, config)
        self.jobs[job_id] = job_info

        # Create and start task
        job_info.task = asyncio.create_task(
            self._run_simulation_job(job_id, config, config_hash)
        )

        logger.info(f"Job {job_id} submitted (running_jobs={running_jobs + 1})")
        return job_id

    async def submit_monte_carlo_job(self, config: Dict[str, Any]) -> str:
        """
        Submit a new Monte Carlo simulation job.

        Args:
            config: Simulation configuration with monte_carlo settings

        Returns:
            Job ID

        Raises:
            RuntimeError: If too many concurrent jobs
            ValueError: If monte_carlo config missing
        """
        if "monte_carlo" not in config or not config["monte_carlo"]:
            raise ValueError("Monte Carlo configuration is required")

        # Check concurrent job limit
        running_jobs = sum(1 for j in self.jobs.values() if j.status == JobStatus.RUNNING)
        if running_jobs >= self.max_concurrent_jobs:
            raise RuntimeError(
                f"Maximum concurrent jobs ({self.max_concurrent_jobs}) reached. "
                f"Try again later."
            )

        # Create job
        job_id = f"mc_{uuid.uuid4().hex[:12]}"
        job_info = JobInfo(job_id, config)
        job_info.is_monte_carlo = True
        job_info.total_months = config["monte_carlo"].get("num_trials", 100)
        self.jobs[job_id] = job_info

        # Create and start task
        job_info.task = asyncio.create_task(
            self._run_monte_carlo_job(job_id, config)
        )

        logger.info(
            f"Monte Carlo job {job_id} submitted with "
            f"{config['monte_carlo']['num_trials']} trials (running_jobs={running_jobs + 1})"
        )
        return job_id

    async def _run_simulation_job(
        self,
        job_id: str,
        config: Dict[str, Any],
        config_hash: str
    ):
        """
        Run simulation job in background.

        Args:
            job_id: Job ID
            config: Simulation configuration
            config_hash: Config hash for caching
        """
        job_info = self.jobs[job_id]

        try:
            # Update status
            job_info.status = JobStatus.RUNNING
            job_info.started_at = datetime.now(timezone.utc)

            logger.info(f"Job {job_id} started")

            # Create simulation loop
            simulation_loop = ABMSimulationLoop.from_config(config)

            # Progress callback
            async def progress_callback(current_month: int, total_months: int):
                job_info.current_month = current_month
                job_info.total_months = total_months
                job_info.progress_pct = (current_month / total_months) * 100.0

            # Run simulation
            results = await simulation_loop.run_full_simulation(
                months=job_info.total_months,
                progress_callback=progress_callback
            )

            # Store results
            job_info.results = results
            job_info.status = JobStatus.COMPLETED
            job_info.completed_at = datetime.now(timezone.utc)

            # Cache results
            self.result_cache[config_hash] = results
            self.cache_ttl[config_hash] = datetime.now(timezone.utc)

            elapsed = (job_info.completed_at - job_info.started_at).total_seconds()
            logger.info(
                f"Job {job_id} completed successfully in {elapsed:.2f}s "
                f"(cached with hash={config_hash})"
            )

        except asyncio.CancelledError:
            job_info.status = JobStatus.CANCELLED
            job_info.completed_at = datetime.now(timezone.utc)
            logger.warning(f"Job {job_id} cancelled")
            raise

        except Exception as e:
            job_info.status = JobStatus.FAILED
            job_info.error = str(e)
            job_info.completed_at = datetime.now(timezone.utc)
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)

    async def _run_monte_carlo_job(self, job_id: str, config: Dict[str, Any]):
        """
        Run Monte Carlo simulation job in background.

        Args:
            job_id: Job ID
            config: Simulation configuration with monte_carlo settings
        """
        job_info = self.jobs[job_id]

        try:
            # Update status
            job_info.status = JobStatus.RUNNING
            job_info.started_at = datetime.now(timezone.utc)

            mc_config = config["monte_carlo"]
            num_trials = mc_config.get("num_trials", 100)

            logger.info(f"Monte Carlo job {job_id} started with {num_trials} trials")

            # Create Monte Carlo engine
            mc_engine = MonteCarloEngine(
                num_trials=num_trials,
                confidence_levels=mc_config.get("confidence_levels", [10, 50, 90]),
                seed=mc_config.get("seed")
            )

            # Progress callback
            async def progress_callback(completed_trials: int, total_trials: int):
                job_info.current_month = completed_trials
                job_info.total_months = total_trials
                job_info.progress_pct = (completed_trials / total_trials) * 100.0

            # Run Monte Carlo simulation
            mc_results = await mc_engine.run_monte_carlo(
                config=config,
                progress_callback=progress_callback
            )

            # Store results
            job_info.mc_results = mc_results
            job_info.status = JobStatus.COMPLETED
            job_info.completed_at = datetime.now(timezone.utc)

            elapsed = (job_info.completed_at - job_info.started_at).total_seconds()
            logger.info(
                f"Monte Carlo job {job_id} completed successfully in {elapsed:.2f}s "
                f"({num_trials} trials, {elapsed/num_trials:.3f}s/trial)"
            )

        except asyncio.CancelledError:
            job_info.status = JobStatus.CANCELLED
            job_info.completed_at = datetime.now(timezone.utc)
            logger.warning(f"Monte Carlo job {job_id} cancelled")
            raise

        except Exception as e:
            job_info.status = JobStatus.FAILED
            job_info.error = str(e)
            job_info.completed_at = datetime.now(timezone.utc)
            logger.error(f"Monte Carlo job {job_id} failed: {e}", exc_info=True)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status.

        Args:
            job_id: Job ID

        Returns:
            Job status dict or None if not found
        """
        job_info = self.jobs.get(job_id)
        if job_info is None:
            return None
        return job_info.to_dict()

    def get_job_results(self, job_id: str) -> Optional[SimulationResults]:
        """
        Get job results.

        Args:
            job_id: Job ID

        Returns:
            SimulationResults or None if not available
        """
        job_info = self.jobs.get(job_id)
        if job_info is None or job_info.status != JobStatus.COMPLETED:
            return None
        return job_info.results

    def get_monte_carlo_results(self, job_id: str) -> Optional[MonteCarloResults]:
        """
        Get Monte Carlo results.

        Args:
            job_id: Job ID

        Returns:
            MonteCarloResults or None if not available
        """
        job_info = self.jobs.get(job_id)
        if job_info is None or job_info.status != JobStatus.COMPLETED:
            return None
        if not job_info.is_monte_carlo:
            return None
        return job_info.mc_results

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Job ID

        Returns:
            True if cancelled, False if not found or not cancellable
        """
        job_info = self.jobs.get(job_id)
        if job_info is None or job_info.status != JobStatus.RUNNING:
            return False

        if job_info.task:
            job_info.task.cancel()
            logger.info(f"Job {job_id} cancellation requested")
            return True

        return False

    def get_all_jobs(self) -> list[Dict[str, Any]]:
        """
        Get all jobs (for admin/monitoring).

        Returns:
            List of job status dicts
        """
        return [job.to_dict() for job in self.jobs.values()]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Stats dictionary
        """
        status_counts = {}
        for status in JobStatus:
            status_counts[status.value] = sum(
                1 for j in self.jobs.values() if j.status == status
            )

        return {
            "total_jobs": len(self.jobs),
            "status_counts": status_counts,
            "cache_size": len(self.result_cache),
            "max_concurrent_jobs": self.max_concurrent_jobs
        }

    async def shutdown(self):
        """Shutdown queue and cleanup."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        # Cancel all running jobs
        for job_info in self.jobs.values():
            if job_info.status == JobStatus.RUNNING and job_info.task:
                job_info.task.cancel()

        logger.info("AsyncJobQueue shutdown complete")
