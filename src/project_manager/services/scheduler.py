"""Background sync scheduler using APScheduler."""

from __future__ import annotations

import atexit
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from project_manager.services.sync import RepoSyncService
from project_manager.utils.logging import get_logger

logger = get_logger(__name__)


class SyncScheduler:
    """Manage a periodic background sync job."""

    def __init__(
        self,
        sync_service: RepoSyncService,
        interval_minutes: int = 360,
        enabled: bool = True,
    ) -> None:
        self.sync_service = sync_service
        self.interval_minutes = interval_minutes
        self.enabled = enabled
        self._scheduler: BackgroundScheduler | None = None

    def start(self) -> None:
        if not self.enabled:
            logger.info("Background scheduler is disabled")
            return
        self._scheduler = BackgroundScheduler(daemon=True)
        self._scheduler.add_job(
            self._run_sync,
            "interval",
            minutes=self.interval_minutes,
            id="sync_all",
            next_run_time=datetime.now(timezone.utc),
        )
        self._scheduler.start()
        atexit.register(self.shutdown)
        logger.info(
            "Started background scheduler (interval=%dm)", self.interval_minutes
        )

    def shutdown(self) -> None:
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Background scheduler shut down")

    def get_status(self) -> dict[str, object]:
        if not self.enabled or not self._scheduler:
            return {
                "running": False,
                "sync_interval_minutes": self.interval_minutes,
                "next_sync_at": None,
            }
        job = self._scheduler.get_job("sync_all")
        next_run = job.next_run_time if job else None
        return {
            "running": self._scheduler.running,
            "sync_interval_minutes": self.interval_minutes,
            "next_sync_at": next_run.isoformat() if next_run else None,
        }

    def _run_sync(self) -> None:
        try:
            logger.info("Scheduled sync started")
            result = self.sync_service.sync_all()
            logger.info("Scheduled sync completed: %d synced", result.synced_count)
        except Exception:
            logger.exception("Scheduled sync failed")
