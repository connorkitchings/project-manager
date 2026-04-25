"""Application settings for Project Manager."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _get_int_env(name: str, default: int) -> int:
    """Read an integer environment variable with fallback."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Project-level configuration loaded from environment variables."""

    project_name: str = "Project Manager"
    github_token: str | None = None
    github_api_base_url: str = "https://api.github.com"
    github_timeout_seconds: int = 15
    database_file: str = "data/project_manager.db"
    tracked_repos_file: str = "config/tracked_repos.yaml"
    frontend_dist_dir: str = "ui/dist"
    recent_activity_limit: int = 5
    stale_after_days: int = 30
    sync_interval_minutes: int = 360
    scheduler_enabled: bool = True
    stale_data_threshold_hours: int = 48
    github_search_default_limit: int = 10

    @property
    def database_path(self) -> Path:
        """Return the absolute path to the SQLite database file."""
        path = Path(self.database_file)
        if path.is_absolute():
            return path
        return Path(__file__).resolve().parents[3] / path

    @property
    def tracked_repos_path(self) -> Path:
        """Return the absolute path to the tracked repo registry file."""
        path = Path(self.tracked_repos_file)
        if path.is_absolute():
            return path
        return Path(__file__).resolve().parents[3] / path

    @property
    def frontend_dist_path(self) -> Path:
        """Return the absolute path to the built frontend bundle."""
        path = Path(self.frontend_dist_dir)
        if path.is_absolute():
            return path
        return Path(__file__).resolve().parents[3] / path

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables."""
        return cls(
            project_name=os.getenv("PROJECT_MANAGER_PROJECT_NAME", "Project Manager"),
            github_token=os.getenv("PROJECT_MANAGER_GITHUB_TOKEN"),
            github_api_base_url=os.getenv(
                "PROJECT_MANAGER_GITHUB_API_BASE_URL", "https://api.github.com"
            ),
            github_timeout_seconds=_get_int_env(
                "PROJECT_MANAGER_GITHUB_TIMEOUT_SECONDS", 15
            ),
            database_file=os.getenv(
                "PROJECT_MANAGER_DATABASE_FILE", "data/project_manager.db"
            ),
            tracked_repos_file=os.getenv(
                "PROJECT_MANAGER_TRACKED_REPOS_FILE", "config/tracked_repos.yaml"
            ),
            frontend_dist_dir=os.getenv("PROJECT_MANAGER_FRONTEND_DIST_DIR", "ui/dist"),
            recent_activity_limit=max(
                1, min(_get_int_env("PROJECT_MANAGER_RECENT_ACTIVITY_LIMIT", 5), 20)
            ),
            stale_after_days=max(
                1, _get_int_env("PROJECT_MANAGER_STALE_AFTER_DAYS", 30)
            ),
            sync_interval_minutes=max(
                5, _get_int_env("PROJECT_MANAGER_SYNC_INTERVAL_MINUTES", 360)
            ),
            scheduler_enabled=os.getenv(
                "PROJECT_MANAGER_SCHEDULER_ENABLED", "true"
            ).lower()
            in ("true", "1", "yes"),
            stale_data_threshold_hours=max(
                1, _get_int_env("PROJECT_MANAGER_STALE_DATA_THRESHOLD_HOURS", 48)
            ),
            github_search_default_limit=max(
                1,
                min(
                    _get_int_env("PROJECT_MANAGER_GITHUB_SEARCH_DEFAULT_LIMIT", 10),
                    30,
                ),
            ),
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached application settings instance."""
    return Settings.from_env()
