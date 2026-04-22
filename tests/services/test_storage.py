"""Tests for SQLite-backed app state storage."""

from datetime import datetime, timezone

from project_manager.models import GitHubEvent, RepoDetail, TrackedRepo
from project_manager.services.storage import SQLiteAppStateStore


def test_bootstrap_persists_tracked_repos(tmp_path):
    database_path = tmp_path / "project_manager.db"
    store = SQLiteAppStateStore(database_path)

    store.bootstrap_tracked_repos(
        [
            TrackedRepo(
                id="project-manager",
                owner="connorkitchings",
                repo="project-manager",
                name="Project Manager",
            )
        ]
    )

    repos = store.list_enabled_repos()

    assert len(repos) == 1
    assert repos[0].id == "project-manager"


def test_snapshot_round_trip(tmp_path):
    now = datetime.now(timezone.utc)
    database_path = tmp_path / "project_manager.db"
    store = SQLiteAppStateStore(database_path)
    store.bootstrap_tracked_repos(
        [
            TrackedRepo(
                id="project-manager",
                owner="connorkitchings",
                repo="project-manager",
                name="Project Manager",
            )
        ]
    )

    snapshot = RepoDetail(
        id="project-manager",
        name="Project Manager",
        full_name="connorkitchings/project-manager",
        current_goal="Ship SQLite persistence",
        status_summary="Backend state is now durable.",
        milestone="Persistence",
        last_activity_at=now,
        attention_flag=False,
        attention_reasons=[],
        missing_sources=[],
        last_synced_at=now,
        recent_updates=["Commit: Add SQLite store"],
        blockers=[],
        github_activity=[
            GitHubEvent(
                type="commit",
                title="Add SQLite store",
                url="https://example.com/commit/1",
                occurred_at=now,
            )
        ],
        documentation_sources=["README.md"],
    )

    store.upsert_snapshot(snapshot)

    reloaded = SQLiteAppStateStore(database_path).get_snapshot("project-manager")

    assert reloaded is not None
    assert reloaded.current_goal == "Ship SQLite persistence"
    assert reloaded.github_activity[0].title == "Add SQLite store"
    assert reloaded.attention_reasons == []
    assert reloaded.last_synced_at == now


def test_create_and_update_tracked_repo(tmp_path):
    database_path = tmp_path / "project_manager.db"
    store = SQLiteAppStateStore(database_path)

    created = store.create_tracked_repo(
        TrackedRepo(
            id="panicstats",
            owner="connorkitchings",
            repo="panicstats",
            name="Panic Stats",
            enabled=False,
            notes="Disabled during cleanup",
        )
    )

    assert created.enabled is False

    updated = store.update_tracked_repo(
        "panicstats",
        enabled=True,
        name="PanicStats",
        notes="Back in rotation",
    )

    assert updated.enabled is True
    assert updated.name == "PanicStats"
    assert updated.notes == "Back in rotation"
    assert [repo.id for repo in store.list_tracked_repos()] == ["panicstats"]
    assert [repo.id for repo in store.list_enabled_repos()] == ["panicstats"]


def test_bootstrap_preserves_runtime_managed_fields(tmp_path):
    database_path = tmp_path / "project_manager.db"
    store = SQLiteAppStateStore(database_path)
    store.create_tracked_repo(
        TrackedRepo(
            id="project-manager",
            owner="connorkitchings",
            repo="project-manager",
            name="Custom runtime name",
            enabled=False,
            notes="Runtime override",
        )
    )

    store.bootstrap_tracked_repos(
        [
            TrackedRepo(
                id="project-manager",
                owner="connorkitchings",
                repo="project-manager",
                name="Seed name",
                enabled=True,
                notes="Seed note",
            )
        ]
    )

    repo = store.get_tracked_repo("project-manager", include_disabled=True)

    assert repo.name == "Custom runtime name"
    assert repo.enabled is False
    assert repo.notes == "Runtime override"
