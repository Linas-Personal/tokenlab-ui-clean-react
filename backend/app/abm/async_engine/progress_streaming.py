"""
Server-Sent Events (SSE) Progress Streaming.

Enables real-time progress updates for long-running simulations.
"""
import asyncio
import json
from typing import Optional, AsyncGenerator
import logging

from app.abm.async_engine.job_queue import AsyncJobQueue, JobStatus

logger = logging.getLogger(__name__)


class ProgressStreamer:
    """
    SSE-based progress streaming for ABM simulations.

    Clients can connect to a stream endpoint and receive real-time
    progress updates as the simulation executes.
    """

    def __init__(self, job_queue: AsyncJobQueue):
        """
        Initialize progress streamer.

        Args:
            job_queue: Job queue instance to monitor
        """
        self.job_queue = job_queue

    async def stream_job_progress(
        self,
        job_id: str,
        poll_interval: float = 0.5
    ) -> AsyncGenerator[str, None]:
        """
        Stream progress updates for a job via SSE.

        Args:
            job_id: Job ID to monitor
            poll_interval: Polling interval in seconds

        Yields:
            SSE-formatted messages
        """
        logger.info(f"Starting progress stream for job {job_id}")

        # Check if job exists
        job_status = self.job_queue.get_job_status(job_id)
        if job_status is None:
            yield self._format_sse_message({
                "type": "error",
                "message": f"Job {job_id} not found"
            })
            return

        # Stream progress until completion
        while True:
            job_status = self.job_queue.get_job_status(job_id)

            if job_status is None:
                yield self._format_sse_message({
                    "type": "error",
                    "message": "Job disappeared"
                })
                break

            # Send progress update
            yield self._format_sse_message({
                "type": "progress",
                "job_id": job_id,
                "status": job_status["status"],
                "progress_pct": job_status["progress_pct"],
                "current_month": job_status["current_month"],
                "total_months": job_status["total_months"]
            })

            # Check if job is done
            if job_status["status"] in ["completed", "failed", "cancelled"]:
                yield self._format_sse_message({
                    "type": "done",
                    "job_id": job_id,
                    "status": job_status["status"],
                    "error": job_status.get("error")
                })
                logger.info(f"Progress stream ended for job {job_id}: {job_status['status']}")
                break

            # Wait before next poll
            await asyncio.sleep(poll_interval)

    def _format_sse_message(self, data: dict) -> str:
        """
        Format message for SSE protocol.

        Args:
            data: Data dictionary

        Returns:
            SSE-formatted string
        """
        json_data = json.dumps(data)
        return f"data: {json_data}\n\n"

    async def stream_multiple_jobs(
        self,
        job_ids: list[str],
        poll_interval: float = 1.0
    ) -> AsyncGenerator[str, None]:
        """
        Stream progress for multiple jobs simultaneously.

        Args:
            job_ids: List of job IDs to monitor
            poll_interval: Polling interval in seconds

        Yields:
            SSE-formatted messages
        """
        logger.info(f"Starting multi-job progress stream for {len(job_ids)} jobs")

        active_jobs = set(job_ids)

        while active_jobs:
            updates = []

            for job_id in list(active_jobs):
                job_status = self.job_queue.get_job_status(job_id)

                if job_status is None:
                    active_jobs.remove(job_id)
                    continue

                updates.append({
                    "job_id": job_id,
                    "status": job_status["status"],
                    "progress_pct": job_status["progress_pct"],
                    "current_month": job_status["current_month"],
                    "total_months": job_status["total_months"]
                })

                # Remove completed jobs from active set
                if job_status["status"] in ["completed", "failed", "cancelled"]:
                    active_jobs.remove(job_id)

            # Send batch update
            if updates:
                yield self._format_sse_message({
                    "type": "batch_progress",
                    "jobs": updates
                })

            # Wait before next poll
            await asyncio.sleep(poll_interval)

        logger.info("Multi-job progress stream ended")

    async def stream_queue_stats(
        self,
        poll_interval: float = 2.0
    ) -> AsyncGenerator[str, None]:
        """
        Stream queue statistics (for monitoring/admin).

        Args:
            poll_interval: Polling interval in seconds

        Yields:
            SSE-formatted messages with queue stats
        """
        logger.info("Starting queue stats stream")

        try:
            while True:
                stats = self.job_queue.get_stats()

                yield self._format_sse_message({
                    "type": "queue_stats",
                    "stats": stats
                })

                await asyncio.sleep(poll_interval)

        except asyncio.CancelledError:
            logger.info("Queue stats stream cancelled")
            raise
