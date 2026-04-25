"""Service construction helpers for the Flask app."""

from functools import lru_cache

from project_manager.core.settings import Settings, get_settings
from project_manager.services.docs import RepositoryDocsReader
from project_manager.services.github import GitHubClient
from project_manager.services.normalizer import RepoStatusNormalizer
from project_manager.services.registry import RegistryService
from project_manager.services.scheduler import SyncScheduler
from project_manager.services.storage import SQLiteAppStateStore
from project_manager.services.sync import RepoSyncService


@lru_cache
def get_registry_service() -> RegistryService:
    settings = get_settings()
    return RegistryService(settings.tracked_repos_path)


@lru_cache
def get_github_client() -> GitHubClient:
    return GitHubClient(get_settings())


@lru_cache
def get_docs_reader() -> RepositoryDocsReader:
    return RepositoryDocsReader(get_github_client())


@lru_cache
def get_normalizer() -> RepoStatusNormalizer:
    return RepoStatusNormalizer(get_settings())


@lru_cache
def get_snapshot_store() -> SQLiteAppStateStore:
    settings = get_settings()
    return SQLiteAppStateStore(settings.database_path)


@lru_cache
def get_sync_service() -> RepoSyncService:
    settings = get_settings()
    return RepoSyncService(
        registry=get_registry_service(),
        github_client=get_github_client(),
        docs_reader=get_docs_reader(),
        normalizer=get_normalizer(),
        snapshot_store=get_snapshot_store(),
        stale_data_threshold_hours=settings.stale_data_threshold_hours,
    )


@lru_cache
def get_sync_scheduler() -> SyncScheduler:
    settings = get_settings()
    return SyncScheduler(
        sync_service=get_sync_service(),
        interval_minutes=settings.sync_interval_minutes,
        enabled=settings.scheduler_enabled,
    )


def get_app_settings() -> Settings:
    """Expose cached app settings for the web layer."""
    return get_settings()
