"""Tests for RepositoryDocsReader."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from project_manager.models import TrackedRepo
from project_manager.services.docs import RepositoryDocsReader


@pytest.fixture
def repo():
    return TrackedRepo(id="x", owner="connorkitchings", repo="project-manager")


def make_reader(get_file_text=None, list_directory=None):
    client = MagicMock()
    if get_file_text is not None:
        client.get_file_text.side_effect = get_file_text
    if list_directory is not None:
        client.list_directory.side_effect = list_directory
    return RepositoryDocsReader(client)


# ---------------------------------------------------------------------------
# read()
# ---------------------------------------------------------------------------


def test_read_all_docs_present(repo):
    def get_file_text(owner, r, path, ref):
        return {
            "README.md": "# Readme content",
            "docs/project_charter.md": "# Charter",
            "docs/implementation_schedule.md": "# Schedule",
            "session_logs/04-22-2026/1 - Log.md": "# Session",
        }.get(path)

    def list_directory(owner, r, path, ref):
        if path == "session_logs":
            return [
                {"type": "dir", "name": "04-22-2026", "path": "session_logs/04-22-2026"}
            ]
        if path == "session_logs/04-22-2026":
            return [
                {
                    "type": "file",
                    "name": "1 - Log.md",
                    "path": "session_logs/04-22-2026/1 - Log.md",
                }
            ]
        return []

    reader = make_reader(get_file_text, list_directory)
    bundle = reader.read(repo, "main")

    assert bundle.readme == "# Readme content"
    assert bundle.project_charter == "# Charter"
    assert bundle.implementation_schedule == "# Schedule"
    assert bundle.latest_session_log == "# Session"
    assert bundle.missing_sources == []
    assert len(bundle.documentation_sources) == 4


def test_read_missing_charter_and_schedule(repo):
    def get_file_text(owner, r, path, ref):
        return {"README.md": "# Readme"}.get(path)

    reader = make_reader(
        get_file_text=get_file_text,
        list_directory=lambda *a: [],
    )
    bundle = reader.read(repo, "main")

    assert bundle.readme == "# Readme"
    assert bundle.project_charter is None
    assert bundle.implementation_schedule is None
    assert "docs/project_charter.md" in bundle.missing_sources
    assert "docs/implementation_schedule.md" in bundle.missing_sources
    assert "README.md" in bundle.documentation_sources


# ---------------------------------------------------------------------------
# _get_latest_session_log()
# ---------------------------------------------------------------------------


def test_latest_session_log_picks_most_recent_date(repo):
    def list_directory(owner, r, path, ref):
        if path == "session_logs":
            return [
                {
                    "type": "dir",
                    "name": "04-18-2026",
                    "path": "session_logs/04-18-2026",
                },
                {
                    "type": "dir",
                    "name": "04-22-2026",
                    "path": "session_logs/04-22-2026",
                },
                {
                    "type": "dir",
                    "name": "04-20-2026",
                    "path": "session_logs/04-20-2026",
                },
            ]
        if path == "session_logs/04-22-2026":
            return [
                {
                    "type": "file",
                    "name": "1 - Log.md",
                    "path": "session_logs/04-22-2026/1 - Log.md",
                }
            ]
        return []

    client = MagicMock()
    client.list_directory.side_effect = list_directory
    client.get_file_text.return_value = "# Latest log"
    reader = RepositoryDocsReader(client)

    result = reader._get_latest_session_log(repo, "main")
    assert result == "# Latest log"
    # Verify it read from the most recent directory
    call_args = client.get_file_text.call_args
    assert "04-22-2026" in call_args.args[2]


def test_latest_session_log_returns_none_for_empty_dir(repo):
    reader = make_reader(list_directory=lambda *a: [])
    result = reader._get_latest_session_log(repo, "main")
    assert result is None


def test_latest_session_log_skips_readme_and_template(repo):
    def list_directory(owner, r, path, ref):
        if path == "session_logs":
            return [
                {"type": "dir", "name": "04-22-2026", "path": "session_logs/04-22-2026"}
            ]
        return [
            {
                "type": "file",
                "name": "README.md",
                "path": "session_logs/04-22-2026/README.md",
            },
            {
                "type": "file",
                "name": "TEMPLATE.md",
                "path": "session_logs/04-22-2026/TEMPLATE.md",
            },
        ]

    reader = make_reader(list_directory=list_directory)
    result = reader._get_latest_session_log(repo, "main")
    assert result is None


def test_latest_session_log_ignores_non_dir_entries(repo):
    def list_directory(owner, r, path, ref):
        if path == "session_logs":
            return [
                {"type": "file", "name": "README.md", "path": "session_logs/README.md"},
                {
                    "type": "dir",
                    "name": "not-a-date",
                    "path": "session_logs/not-a-date",
                },
            ]
        return []

    reader = make_reader(list_directory=list_directory)
    result = reader._get_latest_session_log(repo, "main")
    assert result is None


# ---------------------------------------------------------------------------
# _parse_session_log_dir()
# ---------------------------------------------------------------------------


def test_parse_session_log_dir_mm_dd_yyyy():
    result = RepositoryDocsReader._parse_session_log_dir("04-22-2026")
    assert isinstance(result, datetime)
    assert result.month == 4
    assert result.day == 22
    assert result.year == 2026


def test_parse_session_log_dir_yyyy_mm_dd():
    result = RepositoryDocsReader._parse_session_log_dir("2026-04-22")
    assert isinstance(result, datetime)
    assert result.year == 2026
    assert result.month == 4
    assert result.day == 22


def test_parse_session_log_dir_invalid():
    assert RepositoryDocsReader._parse_session_log_dir("not-a-date") is None
    assert RepositoryDocsReader._parse_session_log_dir("Session 1") is None
    assert RepositoryDocsReader._parse_session_log_dir("") is None
