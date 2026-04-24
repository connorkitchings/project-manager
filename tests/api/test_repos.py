"""API tests for the repository status backend."""

from datetime import datetime, timezone
from pathlib import Path

from project_manager.api.main import create_app
from project_manager.models import RepoDetail, SyncResponse, SyncResult, TrackedRepo
from project_manager.services.github import GitHubAPIError
from project_manager.services.storage import (
    TrackedRepoExistsError,
    TrackedRepoNotFoundError,
)


class FakeSnapshotStore:
    """Minimal persistence stub for API route tests."""

    def get_latest_sync_run(self):
        return None


class FakeSyncService:
    """Minimal fake sync service for route tests."""

    def __init__(self) -> None:
        now = datetime.now(timezone.utc)
        self.snapshot_store = FakeSnapshotStore()
        self.tracked_repos = {
            "project-manager": TrackedRepo(
                id="project-manager",
                owner="connorkitchings",
                repo="project-manager",
                name="Project Manager",
                enabled=True,
                notes="Primary tracked repo",
            ),
            "legacy-repo": TrackedRepo(
                id="legacy-repo",
                owner="connorkitchings",
                repo="legacy-repo",
                name="Legacy Repo",
                enabled=False,
                notes=None,
            ),
        }
        self.detail = RepoDetail(
            id="project-manager",
            name="Project Manager",
            full_name="connorkitchings/project-manager",
            current_goal="Implement backend MVP",
            status_summary="Docs-first repo dashboard backend.",
            milestone="Backend MVP",
            last_activity_at=now,
            attention_flag=False,
            attention_reasons=[],
            missing_sources=[],
            last_synced_at=now,
            recent_updates=["Commit: Implement backend MVP"],
            blockers=[],
            documentation_sources=["README.md"],
        )

    def list_repo_summaries(self):
        return [self.detail.to_summary()]

    def list_tracked_repos(self):
        return list(self.tracked_repos.values())

    def get_repo_detail(self, repo_id: str):
        if repo_id != "project-manager":
            raise TrackedRepoNotFoundError("Tracked repo not found: missing")
        return self.detail

    def create_tracked_repo(
        self,
        *,
        repo_id: str,
        owner: str,
        repo: str,
        name: str | None = None,
        notes: str | None = None,
        enabled: bool = True,
    ):
        tracked_repo = TrackedRepo(
            id=repo_id,
            owner=owner,
            repo=repo,
            name=name,
            enabled=enabled,
            notes=notes,
        )
        self.tracked_repos[repo_id] = tracked_repo
        return tracked_repo

    def update_tracked_repo(self, repo_id: str, **updates):
        repo = self.tracked_repos[repo_id]
        updated = TrackedRepo(
            id=repo.id,
            owner=repo.owner,
            repo=repo.repo,
            name=updates.get("name", repo.name),
            enabled=updates.get("enabled", repo.enabled),
            notes=updates.get("notes", repo.notes),
        )
        self.tracked_repos[repo_id] = updated
        return updated

    def delete_tracked_repo(self, repo_id: str):
        if repo_id not in self.tracked_repos:
            raise TrackedRepoNotFoundError(f"Tracked repo not found: {repo_id}")
        del self.tracked_repos[repo_id]

    def sync_all(self):
        return SyncResponse(
            results=[SyncResult(repo_id="project-manager", synced=True)],
            synced_count=1,
        )


def make_frontend_dist(tmp_path: Path) -> Path:
    """Create a minimal built frontend directory for Flask route tests."""
    frontend_dir = tmp_path / "dist"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text(
        "<!doctype html><html><body><div id='root'></div></body></html>",
        encoding="utf-8",
    )
    (frontend_dir / "assets").mkdir()
    (frontend_dir / "assets" / "app.js").write_text(
        "console.log('hello');",
        encoding="utf-8",
    )
    return frontend_dir


def test_meta_endpoint(tmp_path):
    app = create_app(
        sync_service=FakeSyncService(),
        frontend_dir=make_frontend_dist(tmp_path),
    )
    client = app.test_client()

    response = client.get("/api/meta")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["name"] == "Project Manager"
    assert payload["persistence"] == "sqlite"


def test_repo_endpoints(tmp_path):
    app = create_app(
        sync_service=FakeSyncService(),
        frontend_dir=make_frontend_dist(tmp_path),
    )
    client = app.test_client()

    response = client.get("/api/repos")
    assert response.status_code == 200
    assert response.get_json()["repos"][0]["id"] == "project-manager"

    detail = client.get("/api/repos/project-manager")
    assert detail.status_code == 200
    assert detail.get_json()["current_goal"] == "Implement backend MVP"

    sync = client.post("/api/sync")
    assert sync.status_code == 200
    assert sync.get_json()["synced_count"] == 1

    missing = client.get("/api/repos/missing")
    assert missing.status_code == 404


def test_tracked_repo_management_endpoints(tmp_path):
    app = create_app(
        sync_service=FakeSyncService(),
        frontend_dir=make_frontend_dist(tmp_path),
    )
    client = app.test_client()

    listing = client.get("/api/tracked-repos")
    assert listing.status_code == 200
    assert len(listing.get_json()["tracked_repos"]) == 2

    created = client.post(
        "/api/tracked-repos",
        json={
            "id": "panicstats",
            "owner": "connorkitchings",
            "repo": "panicstats",
            "name": "Panic Stats",
            "enabled": True,
        },
    )
    assert created.status_code == 201
    assert created.get_json()["id"] == "panicstats"

    updated = client.patch(
        "/api/tracked-repos/legacy-repo",
        json={"enabled": True, "notes": "Re-enabled"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["enabled"] is True
    assert updated.get_json()["notes"] == "Re-enabled"


def test_delete_tracked_repo_endpoint(tmp_path):
    app = create_app(
        sync_service=FakeSyncService(),
        frontend_dir=make_frontend_dist(tmp_path),
    )
    client = app.test_client()

    response = client.delete("/api/tracked-repos/project-manager")
    assert response.status_code == 204
    assert response.data == b""

    response = client.delete("/api/tracked-repos/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.get_json()["detail"].lower()


def test_frontend_routes_serve_spa(tmp_path):
    app = create_app(
        sync_service=FakeSyncService(),
        frontend_dir=make_frontend_dist(tmp_path),
    )
    client = app.test_client()

    root = client.get("/")
    assert root.status_code == 200
    assert "text/html" in root.content_type

    detail = client.get("/repos/project-manager")
    assert detail.status_code == 200
    assert "text/html" in detail.content_type

    asset = client.get("/assets/app.js")
    assert asset.status_code == 200
    assert "javascript" in asset.content_type


def test_create_tracked_repo_invalid_id_type_returns_400(tmp_path):
    app = create_app(
        sync_service=FakeSyncService(),
        frontend_dir=make_frontend_dist(tmp_path),
    )
    client = app.test_client()

    response = client.post(
        "/api/tracked-repos",
        json={"id": 123, "owner": "owner", "repo": "repo"},
    )
    assert response.status_code == 400
    assert "detail" in response.get_json()


def test_create_tracked_repo_invalid_enabled_type_returns_400(tmp_path):
    app = create_app(
        sync_service=FakeSyncService(),
        frontend_dir=make_frontend_dist(tmp_path),
    )
    client = app.test_client()

    response = client.post(
        "/api/tracked-repos",
        json={"id": "x", "owner": "o", "repo": "r", "enabled": "yes"},
    )
    assert response.status_code == 400


def test_create_tracked_repo_non_json_body_returns_400(tmp_path):
    app = create_app(
        sync_service=FakeSyncService(),
        frontend_dir=make_frontend_dist(tmp_path),
    )
    client = app.test_client()

    response = client.post(
        "/api/tracked-repos",
        data="not json",
        content_type="application/json",
    )
    assert response.status_code == 400


def test_create_tracked_repo_conflict_returns_409(tmp_path):
    class ConflictSyncService(FakeSyncService):
        def create_tracked_repo(self, **kwargs):
            raise TrackedRepoExistsError("Already exists")

    app = create_app(
        sync_service=ConflictSyncService(),
        frontend_dir=make_frontend_dist(tmp_path),
    )
    client = app.test_client()

    response = client.post(
        "/api/tracked-repos",
        json={"id": "x", "owner": "o", "repo": "r"},
    )
    assert response.status_code == 409


def test_create_tracked_repo_github_error_returns_502(tmp_path):
    class GithubErrorSyncService(FakeSyncService):
        def create_tracked_repo(self, **kwargs):
            raise GitHubAPIError("rate limit", status_code=403)

    app = create_app(
        sync_service=GithubErrorSyncService(),
        frontend_dir=make_frontend_dist(tmp_path),
    )
    client = app.test_client()

    response = client.post(
        "/api/tracked-repos",
        json={"id": "x", "owner": "o", "repo": "r"},
    )
    assert response.status_code == 502


def test_update_tracked_repo_not_found_returns_404(tmp_path):
    class NotFoundSyncService(FakeSyncService):
        def update_tracked_repo(self, repo_id, **updates):
            raise TrackedRepoNotFoundError("not found")

    app = create_app(
        sync_service=NotFoundSyncService(),
        frontend_dir=make_frontend_dist(tmp_path),
    )
    client = app.test_client()

    response = client.patch("/api/tracked-repos/nonexistent", json={"enabled": True})
    assert response.status_code == 404


def test_update_tracked_repo_bad_enabled_type_returns_400(tmp_path):
    app = create_app(
        sync_service=FakeSyncService(),
        frontend_dir=make_frontend_dist(tmp_path),
    )
    client = app.test_client()

    response = client.patch(
        "/api/tracked-repos/project-manager",
        json={"enabled": "true"},
    )
    assert response.status_code == 400
