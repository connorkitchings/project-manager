"""Tracked repository registry loading."""

from __future__ import annotations

from pathlib import Path

import yaml

from project_manager.models import TrackedRepo


class RegistryError(RuntimeError):
    """Raised when the tracked repo registry is invalid."""


class RegistryService:
    """Load tracked repositories from a YAML file."""

    def __init__(self, registry_path: Path) -> None:
        self.registry_path = registry_path

    def load_all(self) -> list[TrackedRepo]:
        """Load all configured tracked repos."""
        if not self.registry_path.exists():
            raise RegistryError(
                f"Tracked repo registry not found: {self.registry_path}"
            )

        data = yaml.safe_load(self.registry_path.read_text()) or {}
        repo_entries = data.get("tracked_repos", [])
        if not isinstance(repo_entries, list):
            raise RegistryError("tracked_repos must be a list")

        return [TrackedRepo.from_dict(entry) for entry in repo_entries]

    def load_enabled(self) -> list[TrackedRepo]:
        """Load only enabled tracked repos."""
        return [repo for repo in self.load_all() if repo.enabled]

    def get(self, repo_id: str) -> TrackedRepo:
        """Get one tracked repo by id."""
        for repo in self.load_all():
            if repo.id == repo_id and repo.enabled:
                return repo
        raise KeyError(f"Tracked repo not found: {repo_id}")
