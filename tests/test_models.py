"""Unit tests for model dataclasses and their serialization methods."""

from datetime import datetime, timezone

from project_manager.models import (
    GitHubActivity,
    GitHubEvent,
    RepoDetail,
    RepoListResponse,
    RepoStatus,
    RepoSummary,
    SyncResponse,
    SyncResult,
    TrackedRepo,
)

# ---------------------------------------------------------------------------
# TrackedRepo
# ---------------------------------------------------------------------------


def test_tracked_repo_to_dict():
    repo = TrackedRepo(
        id="project-manager",
        owner="connorkitchings",
        repo="project-manager",
        name="Project Manager",
        enabled=True,
        notes="Primary repo",
    )
    d = repo.to_dict()
    assert d["id"] == "project-manager"
    assert d["full_name"] == "connorkitchings/project-manager"
    assert d["display_name"] == "Project Manager"
    assert d["enabled"] is True
    assert d["notes"] == "Primary repo"


def test_tracked_repo_display_name_falls_back_to_repo():
    repo = TrackedRepo(id="x", owner="owner", repo="my-repo")
    assert repo.display_name == "my-repo"


def test_tracked_repo_from_dict_full():
    d = {
        "id": "panicstats",
        "owner": "connorkitchings",
        "repo": "panicstats",
        "name": "PanicStats",
        "enabled": False,
        "notes": "side project",
    }
    repo = TrackedRepo.from_dict(d)
    assert repo.id == "panicstats"
    assert repo.enabled is False
    assert repo.notes == "side project"


def test_tracked_repo_from_dict_minimal():
    d = {"id": "x", "owner": "o", "repo": "r"}
    repo = TrackedRepo.from_dict(d)
    assert repo.name is None
    assert repo.enabled is True
    assert repo.notes is None


# ---------------------------------------------------------------------------
# GitHubActivity.flattened()
# ---------------------------------------------------------------------------


def test_github_activity_flattened_sorted_descending():
    now = datetime.now(timezone.utc)
    older = datetime(2026, 1, 1, tzinfo=timezone.utc)
    oldest = datetime(2025, 6, 1, tzinfo=timezone.utc)
    activity = GitHubActivity(
        commits=[GitHubEvent(type="commit", title="A", occurred_at=older)],
        pull_requests=[GitHubEvent(type="pull_request", title="B", occurred_at=now)],
        issues=[GitHubEvent(type="issue", title="C", occurred_at=oldest)],
    )
    flat = activity.flattened()
    assert [e.title for e in flat] == ["B", "A", "C"]


def test_github_activity_flattened_handles_none_timestamps():
    activity = GitHubActivity(
        commits=[
            GitHubEvent(type="commit", title="No time", occurred_at=None),
            GitHubEvent(
                type="commit",
                title="Has time",
                occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ),
        ]
    )
    flat = activity.flattened()
    assert flat[0].title == "Has time"
    assert flat[1].title == "No time"


def test_github_activity_flattened_empty():
    assert GitHubActivity().flattened() == []


# ---------------------------------------------------------------------------
# RepoSummary.to_dict()
# ---------------------------------------------------------------------------


def test_repo_summary_to_dict_includes_status():
    now = datetime.now(timezone.utc)
    summary = RepoSummary(
        id="x",
        name="X",
        full_name="o/x",
        status=RepoStatus.blocked,
        last_synced_at=now,
    )
    d = summary.to_dict()
    assert d["status"] == "blocked"
    assert d["last_synced_at"] == now.isoformat()


def test_repo_summary_to_dict_default_status():
    summary = RepoSummary(id="x", name="X", full_name="o/x")
    assert summary.to_dict()["status"] == "unknown"


# ---------------------------------------------------------------------------
# RepoDetail.to_summary()
# ---------------------------------------------------------------------------


def test_repo_detail_to_summary_propagates_status():
    detail = RepoDetail(
        id="x",
        name="X",
        full_name="o/x",
        status=RepoStatus.stalled,
        attention_reasons=["No recent activity"],
    )
    summary = detail.to_summary()
    assert isinstance(summary, RepoSummary)
    assert summary.status == RepoStatus.stalled
    assert summary.attention_reasons == ["No recent activity"]


def test_repo_detail_to_dict_includes_github_activity():
    now = datetime.now(timezone.utc)
    detail = RepoDetail(
        id="x",
        name="X",
        full_name="o/x",
        github_activity=[
            GitHubEvent(
                type="commit",
                title="Fix bug",
                url="https://example.com",
                occurred_at=now,
            )
        ],
    )
    d = detail.to_dict()
    assert len(d["github_activity"]) == 1
    assert d["github_activity"][0]["title"] == "Fix bug"
    assert d["github_activity"][0]["occurred_at"] == now.isoformat()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


def test_repo_list_response_to_dict():
    summaries = [
        RepoSummary(id="a", name="A", full_name="o/a"),
        RepoSummary(id="b", name="B", full_name="o/b"),
    ]
    response = RepoListResponse(repos=summaries)
    d = response.to_dict()
    assert len(d["repos"]) == 2
    assert d["repos"][0]["id"] == "a"


def test_sync_result_to_dict():
    result = SyncResult(repo_id="x", synced=True)
    d = result.to_dict()
    assert d == {"repo_id": "x", "synced": True, "sync_error": None}


def test_sync_response_to_dict():
    response = SyncResponse(
        results=[SyncResult(repo_id="x", synced=False, sync_error="timeout")],
        synced_count=0,
    )
    d = response.to_dict()
    assert d["synced_count"] == 0
    assert d["results"][0]["sync_error"] == "timeout"
