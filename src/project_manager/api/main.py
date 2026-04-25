"""Flask entrypoint for Project Manager."""

from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory

from project_manager.api.dependencies import (
    get_app_settings,
    get_github_client,
    get_sync_scheduler,
    get_sync_service,
)
from project_manager.services.github import GitHubAPIError
from project_manager.services.storage import (
    TrackedRepoExistsError,
    TrackedRepoNotFoundError,
)
from project_manager.services.sync import InvalidTrackedRepoError


def create_app(
    sync_service=None,
    scheduler=None,
    frontend_dir: Path | None = None,
) -> Flask:
    """Create the Project Manager Flask application."""
    app = Flask(__name__, static_folder=None)
    settings = get_app_settings()
    service = sync_service or get_sync_service()
    active_scheduler = scheduler or get_sync_scheduler()
    resolved_frontend_dir = frontend_dir or settings.frontend_dist_path
    index_file = resolved_frontend_dir / "index.html"

    def _get_json_payload() -> dict:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            raise InvalidTrackedRepoError("Request body must be a JSON object.")
        return payload

    @app.get("/api/meta")
    def api_meta():
        latest_sync_run = service.snapshot_store.get_latest_sync_run()
        scheduler_status = active_scheduler.get_status()
        return jsonify(
            {
                "name": settings.project_name,
                "status": "ok",
                "persistence": "sqlite",
                "database_file": str(settings.database_path),
                "tracked_repos_file": str(settings.tracked_repos_path),
                "latest_sync_run": latest_sync_run,
                "scheduler": scheduler_status,
            }
        )

    @app.get("/api/repos")
    def list_repos():
        return jsonify(
            {"repos": [repo.to_dict() for repo in service.list_repo_summaries()]}
        )

    @app.get("/api/tracked-repos")
    def list_tracked_repos():
        return jsonify(
            {"tracked_repos": [repo.to_dict() for repo in service.list_tracked_repos()]}
        )

    @app.post("/api/tracked-repos")
    def create_tracked_repo():
        try:
            payload = _get_json_payload()
            repo_id = payload.get("id", "")
            owner = payload.get("owner", "")
            repo = payload.get("repo", "")
            if not isinstance(repo_id, str):
                raise InvalidTrackedRepoError("'id' must be a string.")
            if not isinstance(owner, str):
                raise InvalidTrackedRepoError("'owner' must be a string.")
            if not isinstance(repo, str):
                raise InvalidTrackedRepoError("'repo' must be a string.")
            enabled = payload.get("enabled", True)
            if not isinstance(enabled, bool):
                raise InvalidTrackedRepoError("'enabled' must be a boolean.")

            name = payload.get("name")
            if name is not None and not isinstance(name, str):
                raise InvalidTrackedRepoError("'name' must be a string or null.")

            notes = payload.get("notes")
            if notes is not None and not isinstance(notes, str):
                raise InvalidTrackedRepoError("'notes' must be a string or null.")

            tracked_repo = service.create_tracked_repo(
                repo_id=repo_id,
                owner=owner,
                repo=repo,
                name=name,
                notes=notes,
                enabled=enabled,
            )
        except InvalidTrackedRepoError as exc:
            return jsonify({"detail": str(exc)}), 400
        except TrackedRepoExistsError as exc:
            return jsonify({"detail": str(exc)}), 409
        except GitHubAPIError as exc:
            return jsonify({"detail": str(exc)}), 502
        return jsonify(tracked_repo.to_dict()), 201

    @app.patch("/api/tracked-repos/<repo_id>")
    def update_tracked_repo(repo_id: str):
        try:
            payload = _get_json_payload()
            updates: dict[str, object] = {}
            if "enabled" in payload:
                enabled = payload["enabled"]
                if not isinstance(enabled, bool):
                    raise InvalidTrackedRepoError("'enabled' must be a boolean.")
                updates["enabled"] = enabled
            if "name" in payload:
                name = payload["name"]
                if name is not None and not isinstance(name, str):
                    raise InvalidTrackedRepoError("'name' must be a string or null.")
                updates["name"] = name
            if "notes" in payload:
                notes = payload["notes"]
                if notes is not None and not isinstance(notes, str):
                    raise InvalidTrackedRepoError("'notes' must be a string or null.")
                updates["notes"] = notes
            tracked_repo = service.update_tracked_repo(repo_id, **updates)
        except InvalidTrackedRepoError as exc:
            return jsonify({"detail": str(exc)}), 400
        except TrackedRepoNotFoundError as exc:
            return jsonify({"detail": str(exc)}), 404
        return jsonify(tracked_repo.to_dict())

    @app.delete("/api/tracked-repos/<repo_id>")
    def delete_tracked_repo(repo_id: str):
        try:
            service.delete_tracked_repo(repo_id)
        except TrackedRepoNotFoundError:
            return jsonify({"detail": f"Tracked repo not found: {repo_id}"}), 404
        return "", 204

    @app.get("/api/github/search")
    def github_search():
        query = request.args.get("q", "").strip()
        if not query:
            return jsonify({"detail": "Query parameter 'q' is required."}), 400
        try:
            limit = int(
                request.args.get("per_page", settings.github_search_default_limit)
            )
            limit = max(1, min(limit, 30))
        except (ValueError, TypeError):
            limit = settings.github_search_default_limit
        try:
            github = get_github_client()
            results = github.search_repositories(query, limit=limit)
        except GitHubAPIError as exc:
            return jsonify({"detail": str(exc)}), 502
        return jsonify({"results": [r.to_dict() for r in results]})

    @app.get("/api/github/user-repos")
    def github_user_repos():
        username = request.args.get("username", "").strip()
        if not username:
            return jsonify({"detail": "Query parameter 'username' is required."}), 400
        try:
            limit = int(request.args.get("per_page", "30"))
            limit = max(1, min(limit, 100))
        except (ValueError, TypeError):
            limit = 30
        try:
            github = get_github_client()
            results = github.list_user_repos(username, limit=limit)
        except GitHubAPIError as exc:
            return jsonify({"detail": str(exc)}), 502
        return jsonify({"results": [r.to_dict() for r in results]})

    @app.get("/api/repos/<repo_id>")
    def get_repo(repo_id: str):
        try:
            snapshot = service.get_repo_detail(repo_id)
        except TrackedRepoNotFoundError:
            return jsonify({"detail": f"Tracked repo not found: {repo_id}"}), 404
        return jsonify(snapshot.to_dict())

    @app.post("/api/sync")
    def sync_repos():
        return jsonify(service.sync_all().to_dict())

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def frontend(path: str):
        if path.startswith("api/"):
            abort(404)
        if not index_file.exists():
            return (
                jsonify(
                    {
                        "detail": (
                            "Frontend build not found. Run 'npm install' and "
                            "'npm run build' in ui/."
                        )
                    }
                ),
                503,
            )
        if path:
            asset_path = resolved_frontend_dir / path
            if asset_path.is_file():
                return send_from_directory(resolved_frontend_dir, path)
        return send_from_directory(resolved_frontend_dir, "index.html")

    active_scheduler.start()

    return app


app = create_app()
