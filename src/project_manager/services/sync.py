"""Sync orchestration on top of persisted app state."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from project_manager.models import (
    RepoDetail,
    RepoSummary,
    SyncResponse,
    SyncResult,
    TrackedRepo,
)
from project_manager.services.docs import RepositoryDocsReader
from project_manager.services.github import GitHubAPIError, GitHubClient
from project_manager.services.normalizer import RepoStatusNormalizer
from project_manager.services.registry import RegistryService
from project_manager.services.storage import SQLiteAppStateStore
from project_manager.utils.logging import get_logger

logger = get_logger(__name__)
TRACKED_REPO_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
_UNSET = object()


class InvalidTrackedRepoError(ValueError):
    """Raised when tracked repo management input is invalid."""


class RepoSyncService:
    """Load tracked repos, sync docs/activity, and serve snapshots."""

    def __init__(
        self,
        *,
        registry: RegistryService,
        github_client: GitHubClient,
        docs_reader: RepositoryDocsReader,
        normalizer: RepoStatusNormalizer,
        snapshot_store: SQLiteAppStateStore,
        stale_data_threshold_hours: int = 48,
    ) -> None:
        self.registry = registry
        self.github_client = github_client
        self.docs_reader = docs_reader
        self.normalizer = normalizer
        self.snapshot_store = snapshot_store
        self._stale_data_threshold = timedelta(hours=stale_data_threshold_hours)
        self._bootstrap_tracked_repos()

    def _bootstrap_tracked_repos(self) -> None:
        """Load tracked repos from YAML into persisted state."""
        repos = self.registry.load_all()
        self.snapshot_store.bootstrap_tracked_repos(repos)
        logger.info("Bootstrapped %s tracked repos into SQLite state", len(repos))

    def list_repo_summaries(self) -> list[RepoSummary]:
        """List summary status for enabled tracked repos."""
        return [
            self.get_repo_detail(repo.id).to_summary()
            for repo in self.snapshot_store.list_enabled_repos()
        ]

    def list_tracked_repos(self) -> list[TrackedRepo]:
        """List all runtime-managed tracked repos."""
        return self.snapshot_store.list_tracked_repos()

    def get_repo_detail(self, repo_id: str) -> RepoDetail:
        """Get detailed status for a tracked repo."""
        repo = self.snapshot_store.get_tracked_repo(repo_id)
        snapshot = self.snapshot_store.get_snapshot(repo_id)
        if snapshot is None:
            return self.normalizer.build_unsynced_snapshot(repo)
        snapshot.is_data_stale = self._is_snapshot_data_stale(snapshot)
        return snapshot

    def _is_snapshot_data_stale(self, snapshot: RepoDetail) -> bool:
        if snapshot.last_synced_at is None:
            return True
        cutoff = datetime.now(timezone.utc) - self._stale_data_threshold
        return snapshot.last_synced_at < cutoff

    def create_tracked_repo(
        self,
        *,
        repo_id: str,
        owner: str,
        repo: str,
        name: str | None = None,
        notes: str | None = None,
        enabled: bool = True,
    ) -> TrackedRepo:
        """Validate and create a new tracked repo."""
        normalized_id = repo_id.strip()
        normalized_owner = owner.strip()
        normalized_repo = repo.strip()
        normalized_name = name.strip() if name else None
        normalized_notes = notes.strip() if notes else None

        self._validate_tracked_repo_identity(
            repo_id=normalized_id,
            owner=normalized_owner,
            repo=normalized_repo,
        )

        try:
            repo_metadata = self.github_client.get_repository(
                normalized_owner,
                normalized_repo,
            )
        except GitHubAPIError as exc:
            if exc.status_code == 404:
                raise InvalidTrackedRepoError(
                    f"GitHub repository not found: {normalized_owner}/{normalized_repo}"
                ) from exc
            raise

        tracked_repo = TrackedRepo(
            id=normalized_id,
            owner=normalized_owner,
            repo=normalized_repo,
            name=normalized_name or repo_metadata.get("name") or normalized_repo,
            enabled=enabled,
            notes=normalized_notes,
        )
        return self.snapshot_store.create_tracked_repo(tracked_repo)

    def update_tracked_repo(
        self,
        repo_id: str,
        *,
        enabled: bool | None = None,
        name: str | None | object = _UNSET,
        notes: str | None | object = _UNSET,
    ) -> TrackedRepo:
        """Update a tracked repo's runtime-managed fields."""
        updates: dict[str, object] = {}
        if enabled is not None:
            updates["enabled"] = enabled
        if name is not _UNSET:
            assert isinstance(name, str) or name is None
            updates["name"] = name.strip() or None if isinstance(name, str) else None
        if notes is not _UNSET:
            assert isinstance(notes, str) or notes is None
            updates["notes"] = notes.strip() or None if isinstance(notes, str) else None
        return self.snapshot_store.update_tracked_repo(repo_id, **updates)

    def delete_tracked_repo(self, repo_id: str) -> None:
        """Remove a tracked repo and its snapshot from persisted state."""
        self.snapshot_store.delete_tracked_repo(repo_id)

    def sync_all(self) -> SyncResponse:
        """Sync all enabled tracked repos and return per-repo outcomes."""
        started_at = datetime.now(timezone.utc)
        logger.info("Starting sync for tracked repositories")
        results: list[SyncResult] = []
        synced_count = 0
        failed_count = 0

        for repo in self.snapshot_store.list_enabled_repos():
            try:
                snapshot = self._sync_repo(repo)
                self.snapshot_store.upsert_snapshot(snapshot)
                results.append(SyncResult(repo_id=repo.id, synced=True))
                synced_count += 1
                logger.info("Synced repo %s successfully", repo.id)
            except Exception as exc:  # noqa: BLE001
                error_message = str(exc)
                snapshot = self.normalizer.build_error_snapshot(
                    repo,
                    error_message,
                    synced_at=datetime.now(timezone.utc),
                )
                self.snapshot_store.upsert_snapshot(snapshot)
                results.append(
                    SyncResult(repo_id=repo.id, synced=False, sync_error=error_message)
                )
                failed_count += 1
                logger.error("Failed to sync repo %s: %s", repo.id, error_message)

        finished_at = datetime.now(timezone.utc)
        self.snapshot_store.record_sync_run(
            started_at=started_at,
            finished_at=finished_at,
            synced_count=synced_count,
            failed_count=failed_count,
        )
        logger.info(
            "Finished sync run: %s succeeded, %s failed",
            synced_count,
            failed_count,
        )

        return SyncResponse(results=results, synced_count=synced_count)

    def _sync_repo(self, repo) -> RepoDetail:
        """Sync one repo and return the normalized snapshot."""
        repo_metadata = self.github_client.get_repository(repo.owner, repo.repo)
        default_branch = repo_metadata["default_branch"]
        docs = self.docs_reader.read(repo, default_branch)
        activity = self.github_client.get_recent_activity(repo.owner, repo.repo)
        return self.normalizer.normalize(
            repo,
            docs,
            activity,
            synced_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _validate_tracked_repo_identity(
        *,
        repo_id: str,
        owner: str,
        repo: str,
    ) -> None:
        """Validate tracked repo identity fields before persistence."""
        if not repo_id or not TRACKED_REPO_ID_PATTERN.match(repo_id):
            raise InvalidTrackedRepoError(
                "Tracked repo id must use lowercase letters, numbers, "
                "hyphens, or underscores."
            )
        if not owner or "/" in owner or any(character.isspace() for character in owner):
            raise InvalidTrackedRepoError(
                "GitHub owner must be a single path segment without spaces."
            )
        if not repo or "/" in repo or any(character.isspace() for character in repo):
            raise InvalidTrackedRepoError(
                "GitHub repo must be a single path segment without spaces."
            )
