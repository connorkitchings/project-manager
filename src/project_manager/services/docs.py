"""Repository documentation loading from GitHub."""

from __future__ import annotations

from datetime import datetime

from project_manager.models import RepoDocumentBundle, TrackedRepo
from project_manager.services.github import GitHubClient


class RepositoryDocsReader:
    """Read the small set of repo documents used for status normalization."""

    def __init__(self, github_client: GitHubClient) -> None:
        self.github_client = github_client

    def read(self, repo: TrackedRepo, ref: str) -> RepoDocumentBundle:
        """Read tracked docs for a repository."""
        readme = self.github_client.get_file_text(
            repo.owner,
            repo.repo,
            "README.md",
            ref,
        )
        charter = self.github_client.get_file_text(
            repo.owner, repo.repo, "docs/project_charter.md", ref
        )
        schedule = self.github_client.get_file_text(
            repo.owner, repo.repo, "docs/implementation_schedule.md", ref
        )
        session_log = self._get_latest_session_log(repo, ref)

        documentation_sources: list[str] = []
        missing_sources: list[str] = []

        for source_name, source_value in [
            ("README.md", readme),
            ("docs/project_charter.md", charter),
            ("docs/implementation_schedule.md", schedule),
            ("session_logs/latest", session_log),
        ]:
            if source_value:
                documentation_sources.append(source_name)
            else:
                missing_sources.append(source_name)

        return RepoDocumentBundle(
            readme=readme,
            project_charter=charter,
            implementation_schedule=schedule,
            latest_session_log=session_log,
            documentation_sources=documentation_sources,
            missing_sources=missing_sources,
        )

    def _get_latest_session_log(self, repo: TrackedRepo, ref: str) -> str | None:
        """Fetch the latest date-based session log if one exists."""
        root_entries = self.github_client.list_directory(
            repo.owner,
            repo.repo,
            "session_logs",
            ref,
        )
        dated_dirs = []
        for entry in root_entries:
            if entry.get("type") != "dir":
                continue
            name = entry.get("name", "")
            parsed = self._parse_session_log_dir(name)
            if parsed is not None:
                dated_dirs.append((parsed, entry))

        if not dated_dirs:
            return None

        latest_dir = sorted(dated_dirs, key=lambda item: item[0], reverse=True)[0][1]
        dir_path = latest_dir["path"]
        log_entries = self.github_client.list_directory(
            repo.owner,
            repo.repo,
            dir_path,
            ref,
        )
        markdown_files = [
            entry
            for entry in log_entries
            if entry.get("type") == "file"
            and entry.get("name", "").endswith(".md")
            and entry.get("name") not in {"README.md", "TEMPLATE.md"}
        ]
        if not markdown_files:
            return None

        markdown_files.sort(key=lambda entry: entry["name"], reverse=True)
        latest_log_path = markdown_files[0]["path"]
        return self.github_client.get_file_text(
            repo.owner,
            repo.repo,
            latest_log_path,
            ref,
        )

    @staticmethod
    def _parse_session_log_dir(name: str) -> datetime | None:
        """Parse supported session log directory naming conventions."""
        for fmt in ("%m-%d-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(name, fmt)
            except ValueError:
                continue
        return None
