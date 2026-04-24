"""Common pytest fixtures for Project Manager tests."""

from datetime import datetime, timezone

import pytest

from project_manager.models import (
    GitHubActivity,
    GitHubEvent,
    RepoDocumentBundle,
    TrackedRepo,
)


@pytest.fixture
def tracked_repo() -> TrackedRepo:
    """Return a representative tracked repo registry entry."""
    return TrackedRepo(
        id="project-manager",
        name="Project Manager",
        owner="connorkitchings",
        repo="project-manager",
        enabled=True,
        notes="Primary tracked repo",
    )


@pytest.fixture
def sample_docs() -> RepoDocumentBundle:
    """Return a representative set of repo docs."""
    return RepoDocumentBundle(
        readme="# Project Manager\n\nInternal dashboard for repo status.\n",
        project_charter=(
            "**Vision:** Give one place to understand tracked repository health.\n\n"
            "**Technical Goal:** Deliver a backend MVP for repo sync.\n"
        ),
        implementation_schedule=(
            "**Current Stage:** Backend MVP\n\n"
            "## Immediate Next Steps\n"
            "1. Build sync service\n"
            "2. Add list/detail APIs\n"
        ),
        latest_session_log=(
            "- **Goal**: Replace template code with backend MVP\n"
            "- **Accomplished**: Reframed the repo around Project Manager\n"
            "- **Blockers**: None\n"
        ),
        documentation_sources=[
            "README.md",
            "docs/project_charter.md",
            "docs/implementation_schedule.md",
            "session_logs/latest",
        ],
        missing_sources=[],
    )


@pytest.fixture
def sample_activity() -> GitHubActivity:
    """Return representative recent GitHub activity."""
    now = datetime.now(timezone.utc)
    return GitHubActivity(
        commits=[
            GitHubEvent(
                type="commit",
                title="Implement backend MVP",
                url="https://example.com/commit/1",
                occurred_at=now,
            )
        ],
        pull_requests=[
            GitHubEvent(
                type="pull_request",
                title="Add repo sync API",
                url="https://example.com/pull/1",
                occurred_at=now,
            )
        ],
        issues=[
            GitHubEvent(
                type="issue",
                title="Track stale repos",
                url="https://example.com/issues/1",
                occurred_at=now,
            )
        ],
        last_activity_at=now,
    )
