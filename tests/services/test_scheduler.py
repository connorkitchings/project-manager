"""Tests for the background sync scheduler."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from project_manager.models import SyncResponse, SyncResult
from project_manager.services.scheduler import SyncScheduler


@pytest.fixture
def mock_sync_service():
    service = MagicMock()
    service.sync_all.return_value = SyncResponse(
        results=[SyncResult(repo_id="test", synced=True)],
        synced_count=1,
    )
    return service


def test_start_creates_running_scheduler(mock_sync_service):
    scheduler = SyncScheduler(mock_sync_service, interval_minutes=60, enabled=True)
    scheduler.start()

    status = scheduler.get_status()
    assert status["running"] is True
    assert status["sync_interval_minutes"] == 60
    assert status["next_sync_at"] is not None

    scheduler.shutdown()


def test_disabled_scheduler_reports_not_running(mock_sync_service):
    scheduler = SyncScheduler(mock_sync_service, interval_minutes=60, enabled=False)
    scheduler.start()

    status = scheduler.get_status()
    assert status["running"] is False
    assert status["sync_interval_minutes"] == 60
    assert status["next_sync_at"] is None


def test_disabled_scheduler_does_not_start(mock_sync_service):
    scheduler = SyncScheduler(mock_sync_service, enabled=False)
    scheduler.start()

    mock_sync_service.sync_all.assert_not_called()


def test_run_sync_calls_sync_service(mock_sync_service):
    scheduler = SyncScheduler(mock_sync_service, interval_minutes=60, enabled=True)
    scheduler._run_sync()

    mock_sync_service.sync_all.assert_called_once()


def test_run_sync_handles_exception(mock_sync_service):
    mock_sync_service.sync_all.side_effect = RuntimeError("boom")
    scheduler = SyncScheduler(mock_sync_service, interval_minutes=60, enabled=True)
    scheduler._run_sync()

    mock_sync_service.sync_all.assert_called_once()


def test_shutdown_stops_scheduler(mock_sync_service):
    scheduler = SyncScheduler(mock_sync_service, interval_minutes=60, enabled=True)
    scheduler.start()
    assert scheduler.get_status()["running"] is True

    scheduler.shutdown()
    assert scheduler.get_status()["running"] is False


def test_get_status_before_start(mock_sync_service):
    scheduler = SyncScheduler(mock_sync_service, interval_minutes=120, enabled=True)
    status = scheduler.get_status()

    assert status["running"] is False
    assert status["sync_interval_minutes"] == 120
    assert status["next_sync_at"] is None


def test_scheduler_interval_from_settings(mock_sync_service):
    scheduler = SyncScheduler(mock_sync_service, interval_minutes=15, enabled=True)
    assert scheduler.interval_minutes == 15
