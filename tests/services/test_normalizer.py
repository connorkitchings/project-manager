"""Tests for repo status normalization."""

from datetime import datetime, timedelta, timezone

from project_manager.core.settings import Settings
from project_manager.models import GitHubActivity, RepoDocumentBundle
from project_manager.services.normalizer import RepoStatusNormalizer


def test_normalizer_builds_snapshot(tracked_repo, sample_docs, sample_activity):
    normalizer = RepoStatusNormalizer(Settings())
    snapshot = normalizer.normalize(
        tracked_repo,
        sample_docs,
        sample_activity,
        synced_at=sample_activity.last_activity_at,
    )

    assert snapshot.id == "project-manager"
    assert snapshot.current_goal == "Replace template code with backend MVP"
    assert snapshot.status_summary == "Internal dashboard for repo status."
    assert snapshot.milestone == "Backend MVP"
    assert snapshot.attention_flag is False
    assert snapshot.attention_reasons == []
    assert snapshot.recent_updates


def test_unsynced_snapshot_is_flagged(tracked_repo):
    normalizer = RepoStatusNormalizer(Settings())
    snapshot = normalizer.build_unsynced_snapshot(tracked_repo)

    assert snapshot.attention_flag is True
    assert snapshot.attention_reasons == ["Not synced yet."]
    assert snapshot.missing_sources == ["not_synced"]


def test_normalizer_handles_non_tldr_session_logs_and_metadata_readmes(
    tracked_repo,
    sample_activity,
):
    normalizer = RepoStatusNormalizer(Settings())
    docs = RepoDocumentBundle(
        readme=(
            "# FRED-Macro-Dashboard\n\n"
            "> **Personal macroeconomic data infrastructure**\n\n"
            "**Version**: 0.1.0\n"
            "**Status**: Stable\n\n"
            "## What This Is\n\n"
            "A personal data pipeline that fetches macroeconomic indicators.\n"
        ),
        project_charter="**Technical Goal:** Deliver a working MVP.\n",
        implementation_schedule=(
            "**Phase:** Post-MVP Stabilization\n"
            "**Next Milestone:** Validate and merge BLS alias coexistence expansion\n"
        ),
        latest_session_log=(
            "# Session Log: Audit Completion\n\n"
            "**Date:** 2026-02-15\n"
            "**Goal:** Complete Code Safety and Docstring Audit.\n\n"
            "## Summary\n"
            "Completed the code safety audit and documentation polish.\n\n"
            "## Final Status\n"
            "- **Safety:** Critical scripts protected.\n"
            "- **Blockers:** None. (Census warnings are expected.)\n"
        ),
        documentation_sources=[
            "README.md",
            "docs/project_charter.md",
            "docs/implementation_schedule.md",
            "session_logs/latest",
        ],
        missing_sources=[],
    )

    snapshot = normalizer.normalize(
        tracked_repo,
        docs,
        sample_activity,
        synced_at=sample_activity.last_activity_at,
    )

    assert snapshot.current_goal == "Complete Code Safety and Docstring Audit"
    assert snapshot.status_summary == (
        "A personal data pipeline that fetches macroeconomic indicators."
    )
    assert snapshot.milestone == "Validate and merge BLS alias coexistence expansion"
    assert snapshot.blockers == []
    assert snapshot.attention_flag is False


def test_normalizer_flags_missing_docs_and_staleness(tracked_repo):
    now = datetime.now(timezone.utc)
    stale_activity = GitHubActivity(last_activity_at=now - timedelta(days=60))
    normalizer = RepoStatusNormalizer(Settings(stale_after_days=30))
    docs = RepoDocumentBundle(
        readme="# PanicStats\n\nA modern, fast, and community-minded tracker.\n",
        latest_session_log="**Goal:** Complete audit prep.\n",
        documentation_sources=["README.md", "session_logs/latest"],
        missing_sources=["docs/project_charter.md", "docs/implementation_schedule.md"],
    )

    snapshot = normalizer.normalize(
        tracked_repo,
        docs,
        stale_activity,
        synced_at=now,
    )

    assert snapshot.attention_flag is True
    assert (
        "Missing docs: docs/project_charter.md, docs/implementation_schedule.md"
        in snapshot.attention_reasons
    )
    assert any(
        "No recent GitHub activity" in reason
        for reason in snapshot.attention_reasons
    )
