"""Background task scheduler using APScheduler."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from ..config import settings


logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages background tasks with APScheduler."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    def start(self):
        """Start the scheduler."""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Task scheduler started")

    def shutdown(self):
        """Shutdown the scheduler."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Task scheduler shutdown")

    def add_interval_job(
        self,
        func,
        minutes: int,
        job_id: str,
        description: str = ""
    ):
        """
        Add a job that runs at fixed intervals.

        Args:
            func: Async function to execute
            minutes: Interval in minutes
            job_id: Unique job identifier
            description: Human-readable description
        """
        try:
            self.scheduler.add_job(
                func,
                trigger=IntervalTrigger(minutes=minutes),
                id=job_id,
                name=description,
                replace_existing=True,
                max_instances=1  # Prevent overlapping executions
            )
            logger.info(f"Added scheduled job: {description} (every {minutes} minutes)")
        except Exception as e:
            logger.error(f"Error adding scheduled job {job_id}: {e}")

    def remove_job(self, job_id: str):
        """Remove a scheduled job."""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed scheduled job: {job_id}")
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")

    def get_jobs(self) -> list:
        """Get list of all scheduled jobs."""
        return self.scheduler.get_jobs()

    def pause_job(self, job_id: str):
        """Pause a scheduled job."""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")

    def resume_job(self, job_id: str):
        """Resume a paused job."""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")


# Global scheduler instance
task_scheduler = TaskScheduler()
