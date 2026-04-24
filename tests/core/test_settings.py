"""Tests for application settings."""

from project_manager.core.settings import get_settings


def test_default_settings(monkeypatch):
    monkeypatch.delenv("PROJECT_MANAGER_PROJECT_NAME", raising=False)
    monkeypatch.delenv("PROJECT_MANAGER_DATABASE_FILE", raising=False)
    monkeypatch.delenv("PROJECT_MANAGER_TRACKED_REPOS_FILE", raising=False)
    monkeypatch.delenv("PROJECT_MANAGER_FRONTEND_DIST_DIR", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.project_name == "Project Manager"
    assert settings.database_path.name == "project_manager.db"
    assert settings.tracked_repos_path.name == "tracked_repos.yaml"
    assert settings.frontend_dist_path.name == "dist"

    get_settings.cache_clear()


def test_environment_overrides(monkeypatch):
    monkeypatch.setenv("PROJECT_MANAGER_PROJECT_NAME", "Custom PM")
    monkeypatch.setenv("PROJECT_MANAGER_DATABASE_FILE", "data/custom.db")
    monkeypatch.setenv("PROJECT_MANAGER_TRACKED_REPOS_FILE", "config/custom.yaml")
    monkeypatch.setenv("PROJECT_MANAGER_FRONTEND_DIST_DIR", "custom-ui/build")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.project_name == "Custom PM"
    assert settings.database_path.name == "custom.db"
    assert settings.tracked_repos_path.name == "custom.yaml"
    assert settings.frontend_dist_path.name == "build"

    get_settings.cache_clear()
