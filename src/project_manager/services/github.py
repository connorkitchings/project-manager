"""GitHub API access for tracked repository syncing."""

from __future__ import annotations

import base64
from datetime import datetime
from typing import Any

import requests

from project_manager.core.settings import Settings
from project_manager.models import GitHubActivity, GitHubEvent


class GitHubAPIError(RuntimeError):
    """Raised when the GitHub API cannot satisfy a request."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _parse_github_datetime(value: str | None) -> datetime | None:
    """Parse GitHub ISO timestamps."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class GitHubClient:
    """Small GitHub REST API client for repo status sync."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": "project-manager",
            }
        )
        if settings.github_token:
            self.session.headers["Authorization"] = f"Bearer {settings.github_token}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        allow_not_found: bool = False,
    ) -> requests.Response | None:
        url = f"{self.settings.github_api_base_url.rstrip('/')}{path}"
        response = self.session.request(
            method,
            url,
            params=params,
            timeout=self.settings.github_timeout_seconds,
        )
        if response.status_code == 404 and allow_not_found:
            return None
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            error_message = response.text
            try:
                payload = response.json()
                error_message = payload.get("message", response.text)
            except ValueError:
                pass
            if response.status_code == 403 and "rate limit" in error_message.lower():
                error_message = (
                    "GitHub API rate limit exceeded. Configure "
                    "PROJECT_MANAGER_GITHUB_TOKEN for multi-repo sync."
                )
            raise GitHubAPIError(
                "GitHub API request failed for "
                f"{path}: {response.status_code} ({error_message})",
                status_code=response.status_code,
            ) from exc
        return response

    def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        """Fetch repository metadata."""
        response = self._request("GET", f"/repos/{owner}/{repo}")
        assert response is not None
        return response.json()

    def get_file_text(self, owner: str, repo: str, path: str, ref: str) -> str | None:
        """Fetch and decode a file from repository contents."""
        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
            allow_not_found=True,
        )
        if response is None:
            return None

        payload = response.json()
        if payload.get("type") != "file":
            return None

        content = payload.get("content")
        if not content:
            return None

        decoded = base64.b64decode(content)
        return decoded.decode("utf-8")

    def list_directory(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str,
    ) -> list[dict[str, Any]]:
        """List directory contents using the repository contents API."""
        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
            allow_not_found=True,
        )
        if response is None:
            return []

        payload = response.json()
        if isinstance(payload, list):
            return payload
        return []

    def get_recent_activity(self, owner: str, repo: str) -> GitHubActivity:
        """Fetch recent commits, pull requests, and issues."""
        limit = self.settings.recent_activity_limit

        commits_response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/commits",
            params={"per_page": limit},
        )
        pulls_response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls",
            params={
                "state": "all",
                "sort": "updated",
                "direction": "desc",
                "per_page": limit,
            },
        )
        issues_response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            params={
                "state": "all",
                "sort": "updated",
                "direction": "desc",
                "per_page": limit,
            },
        )

        commits = [
            GitHubEvent(
                type="commit",
                title=item["commit"]["message"].splitlines()[0],
                url=item.get("html_url"),
                occurred_at=_parse_github_datetime(item["commit"]["committer"]["date"]),
            )
            for item in commits_response.json()
        ]

        pull_requests = [
            GitHubEvent(
                type="pull_request",
                title=item["title"],
                url=item.get("html_url"),
                occurred_at=_parse_github_datetime(item.get("updated_at")),
            )
            for item in pulls_response.json()
        ]

        issues = [
            GitHubEvent(
                type="issue",
                title=item["title"],
                url=item.get("html_url"),
                occurred_at=_parse_github_datetime(item.get("updated_at")),
            )
            for item in issues_response.json()
            if "pull_request" not in item
        ]

        all_events = commits + pull_requests + issues
        last_activity_at = max(
            (event.occurred_at for event in all_events if event.occurred_at),
            default=None,
        )

        return GitHubActivity(
            commits=commits,
            pull_requests=pull_requests,
            issues=issues,
            last_activity_at=last_activity_at,
        )
