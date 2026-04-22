"""Tests for tracked repo registry loading."""

from pathlib import Path

import pytest

from project_manager.services.registry import RegistryError, RegistryService


def test_registry_loads_enabled_and_disabled_repos(tmp_path: Path):
    registry_path = tmp_path / "tracked_repos.yaml"
    registry_path.write_text(
        """
tracked_repos:
  - id: one
    owner: octocat
    repo: alpha
    enabled: true
  - id: two
    owner: octocat
    repo: beta
    enabled: false
"""
    )

    service = RegistryService(registry_path)

    all_repos = service.load_all()
    enabled_repos = service.load_enabled()

    assert len(all_repos) == 2
    assert len(enabled_repos) == 1
    assert enabled_repos[0].id == "one"


def test_registry_rejects_invalid_shape(tmp_path: Path):
    registry_path = tmp_path / "tracked_repos.yaml"
    registry_path.write_text("tracked_repos: invalid")

    service = RegistryService(registry_path)

    with pytest.raises(RegistryError):
        service.load_all()
