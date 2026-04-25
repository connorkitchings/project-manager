"""Tests for sync orchestration."""

from pathlib import Path

from project_manager.core.settings import Settings
from project_manager.services.normalizer import RepoStatusNormalizer
from project_manager.services.storage import SQLiteAppStateStore
from project_manager.services.sync import RepoSyncService


class FakeRegistry:
    def __init__(self, repo):
        self.repo = repo

    def load_all(self):
        return [self.repo]

    def load_enabled(self):
        return [self.repo]

    def get(self, repo_id: str):
        if repo_id != self.repo.id:
            raise KeyError(f"Tracked repo not found: {repo_id}")
        return self.repo


class FakeGitHubClient:
    def __init__(self, activity):
        self.activity = activity
        self.repository_calls: list[tuple[str, str]] = []

    def get_repository(self, owner: str, repo: str):
        self.repository_calls.append((owner, repo))
        return {"default_branch": "main"}

    def get_recent_activity(self, owner: str, repo: str):
        return self.activity


class FakeDocsReader:
    def __init__(self, docs):
        self.docs = docs

    def read(self, repo, ref: str):
        return self.docs


class BrokenGitHubClient(FakeGitHubClient):
    def get_repository(self, owner: str, repo: str):
        raise RuntimeError("boom")


def make_store(tmp_path: Path) -> SQLiteAppStateStore:
    """Create a SQLite app state store in a temp directory."""
    return SQLiteAppStateStore(tmp_path / "project_manager.db")


def test_sync_all_stores_snapshot(
    tracked_repo,
    sample_docs,
    sample_activity,
    tmp_path,
):
    service = RepoSyncService(
        registry=FakeRegistry(tracked_repo),
        github_client=FakeGitHubClient(sample_activity),
        docs_reader=FakeDocsReader(sample_docs),
        normalizer=RepoStatusNormalizer(Settings()),
        snapshot_store=make_store(tmp_path),
    )

    result = service.sync_all()
    detail = service.get_repo_detail("project-manager")

    assert result.synced_count == 1
    assert detail.current_goal == "Replace template code with backend MVP"
    assert detail.last_synced_at is not None


def test_sync_failures_become_error_snapshots(
    tracked_repo,
    sample_docs,
    sample_activity,
    tmp_path,
):
    service = RepoSyncService(
        registry=FakeRegistry(tracked_repo),
        github_client=BrokenGitHubClient(sample_activity),
        docs_reader=FakeDocsReader(sample_docs),
        normalizer=RepoStatusNormalizer(Settings()),
        snapshot_store=make_store(tmp_path),
    )

    result = service.sync_all()
    detail = service.get_repo_detail("project-manager")

    assert result.synced_count == 0
    assert detail.sync_error == "boom"
    assert detail.attention_flag is True


def test_sync_persists_snapshot_across_store_instances(
    tracked_repo,
    sample_docs,
    sample_activity,
    tmp_path,
):
    database_path = tmp_path / "project_manager.db"
    first_service = RepoSyncService(
        registry=FakeRegistry(tracked_repo),
        github_client=FakeGitHubClient(sample_activity),
        docs_reader=FakeDocsReader(sample_docs),
        normalizer=RepoStatusNormalizer(Settings()),
        snapshot_store=SQLiteAppStateStore(database_path),
    )
    first_service.sync_all()

    second_service = RepoSyncService(
        registry=FakeRegistry(tracked_repo),
        github_client=FakeGitHubClient(sample_activity),
        docs_reader=FakeDocsReader(sample_docs),
        normalizer=RepoStatusNormalizer(Settings()),
        snapshot_store=SQLiteAppStateStore(database_path),
    )

    detail = second_service.get_repo_detail("project-manager")

    assert detail.current_goal == "Replace template code with backend MVP"
    assert detail.last_synced_at is not None


def test_create_tracked_repo_uses_github_validation(
    sample_docs,
    sample_activity,
    tmp_path,
):
    github_client = FakeGitHubClient(sample_activity)
    service = RepoSyncService(
        registry=FakeRegistry(
            type(
                "Repo",
                (),
                {
                    "id": "seed-repo",
                    "owner": "connorkitchings",
                    "repo": "seed-repo",
                    "name": "Seed Repo",
                    "enabled": True,
                    "notes": None,
                },
            )()
        ),
        github_client=github_client,
        docs_reader=FakeDocsReader(sample_docs),
        normalizer=RepoStatusNormalizer(Settings()),
        snapshot_store=make_store(tmp_path),
    )

    created = service.create_tracked_repo(
        repo_id="panicstats",
        owner="connorkitchings",
        repo="panicstats",
        enabled=False,
    )

    assert created.id == "panicstats"
    assert created.enabled is False
    assert ("connorkitchings", "panicstats") in github_client.repository_calls


def test_sync_all_skips_disabled_repos(
    tracked_repo,
    sample_docs,
    sample_activity,
    tmp_path,
):
    disabled_repo = type(
        "Repo",
        (),
        {
            "id": "disabled-repo",
            "owner": "connorkitchings",
            "repo": "disabled-repo",
            "name": "Disabled Repo",
            "enabled": False,
            "notes": None,
        },
    )()
    github_client = FakeGitHubClient(sample_activity)
    service = RepoSyncService(
        registry=type(
            "Registry",
            (),
            {
                "load_all": lambda self: [tracked_repo, disabled_repo],
            },
        )(),
        github_client=github_client,
        docs_reader=FakeDocsReader(sample_docs),
        normalizer=RepoStatusNormalizer(Settings()),
        snapshot_store=make_store(tmp_path),
    )

    result = service.sync_all()

    assert result.synced_count == 1
    assert service.snapshot_store.get_snapshot("disabled-repo") is None
    assert ("connorkitchings", "disabled-repo") not in github_client.repository_calls


def test_get_repo_detail_marks_fresh_data_as_not_stale(
    tracked_repo,
    sample_docs,
    sample_activity,
    tmp_path,
):
    service = RepoSyncService(
        registry=FakeRegistry(tracked_repo),
        github_client=FakeGitHubClient(sample_activity),
        docs_reader=FakeDocsReader(sample_docs),
        normalizer=RepoStatusNormalizer(Settings()),
        snapshot_store=make_store(tmp_path),
        stale_data_threshold_hours=48,
    )
    service.sync_all()

    detail = service.get_repo_detail("project-manager")

    assert detail.is_data_stale is False


def test_get_repo_detail_marks_old_data_as_stale(
    tracked_repo,
    sample_docs,
    sample_activity,
    tmp_path,
):
    from datetime import datetime, timezone

    from project_manager.models import RepoDetail

    store = make_store(tmp_path)
    service = RepoSyncService(
        registry=FakeRegistry(tracked_repo),
        github_client=FakeGitHubClient(sample_activity),
        docs_reader=FakeDocsReader(sample_docs),
        normalizer=RepoStatusNormalizer(Settings()),
        snapshot_store=store,
        stale_data_threshold_hours=1,
    )
    service.sync_all()

    old_snapshot = RepoDetail(
        id="project-manager",
        name="Project Manager",
        full_name="connorkitchings/project-manager",
        last_synced_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    store.upsert_snapshot(old_snapshot)

    detail = service.get_repo_detail("project-manager")

    assert detail.is_data_stale is True


def test_get_repo_detail_marks_unsynced_as_stale(tracked_repo, tmp_path):
    store = make_store(tmp_path)
    store.bootstrap_tracked_repos([tracked_repo])
    empty_activity = type(
        "A",
        (),
        {
            "flattened": lambda self: [],
            "last_activity_at": None,
            "commits": [],
            "pull_requests": [],
            "issues": [],
        },
    )()
    empty_docs = type(
        "D",
        (),
        {
            "readme": None,
            "project_charter": None,
            "implementation_schedule": None,
            "latest_session_log": None,
            "documentation_sources": [],
            "missing_sources": [],
        },
    )()
    service = RepoSyncService(
        registry=FakeRegistry(tracked_repo),
        github_client=FakeGitHubClient(empty_activity),
        docs_reader=FakeDocsReader(empty_docs),
        normalizer=RepoStatusNormalizer(Settings()),
        snapshot_store=store,
        stale_data_threshold_hours=48,
    )

    detail = service.get_repo_detail("project-manager")

    assert detail.is_data_stale is False
    assert detail.attention_flag is True
    assert "Not synced yet." in detail.attention_reasons
