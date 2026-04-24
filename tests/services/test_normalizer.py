"""Tests for repo status normalization."""

from datetime import datetime, timedelta, timezone

from project_manager.core.settings import Settings
from project_manager.models import GitHubActivity, RepoDocumentBundle, RepoStatus
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
        "No recent GitHub activity" in reason for reason in snapshot.attention_reasons
    )


def test_normalizer_status_healthy(tracked_repo, sample_docs, sample_activity):
    normalizer = RepoStatusNormalizer(Settings())
    snapshot = normalizer.normalize(
        tracked_repo,
        sample_docs,
        sample_activity,
        synced_at=sample_activity.last_activity_at,
    )
    assert snapshot.status == RepoStatus.healthy


def test_normalizer_status_stalled(tracked_repo, sample_docs):
    now = datetime.now(timezone.utc)
    stale = GitHubActivity(last_activity_at=now - timedelta(days=60))
    normalizer = RepoStatusNormalizer(Settings(stale_after_days=30))
    snapshot = normalizer.normalize(tracked_repo, sample_docs, stale, synced_at=now)
    assert snapshot.status == RepoStatus.stalled


def test_normalizer_status_blocked(tracked_repo, sample_activity):
    now = datetime.now(timezone.utc)
    docs = RepoDocumentBundle(
        readme="# Repo\n\nSome project.\n",
        latest_session_log=(
            "**Goal:** Fix things.\n**Blockers:** CI pipeline is broken.\n"
        ),
        documentation_sources=["README.md"],
        missing_sources=[],
    )
    normalizer = RepoStatusNormalizer(Settings())
    snapshot = normalizer.normalize(tracked_repo, docs, sample_activity, synced_at=now)
    assert snapshot.status == RepoStatus.blocked


def test_normalizer_status_active(tracked_repo, sample_activity):
    now = datetime.now(timezone.utc)
    docs = RepoDocumentBundle(
        readme="# Repo\n\nSome project.\n",
        documentation_sources=["README.md"],
        missing_sources=["docs/project_charter.md"],
    )
    normalizer = RepoStatusNormalizer(Settings())
    snapshot = normalizer.normalize(tracked_repo, docs, sample_activity, synced_at=now)
    assert snapshot.status == RepoStatus.active
    assert snapshot.attention_flag is True


def test_unsynced_snapshot_has_unknown_status(tracked_repo):
    normalizer = RepoStatusNormalizer(Settings())
    snapshot = normalizer.build_unsynced_snapshot(tracked_repo)
    assert snapshot.status == RepoStatus.unknown


def test_error_snapshot_has_error_status(tracked_repo):
    now = datetime.now(timezone.utc)
    normalizer = RepoStatusNormalizer(Settings())
    snapshot = normalizer.build_error_snapshot(tracked_repo, "GitHub rate limit", now)
    assert snapshot.status == RepoStatus.error
    assert snapshot.sync_error == "GitHub rate limit"


# ---------------------------------------------------------------------------
# Static helper method unit tests
# ---------------------------------------------------------------------------


def test_extract_session_field_with_colon():
    text = "- **Goal:** Build the MVP"
    assert RepoStatusNormalizer._extract_session_field(text, "Goal") == "Build the MVP"


def test_extract_session_field_without_colon():
    text = "**Goal** Refactor the parser"
    assert (
        RepoStatusNormalizer._extract_session_field(text, "Goal")
        == "Refactor the parser"
    )


def test_extract_session_field_returns_none_for_missing():
    assert RepoStatusNormalizer._extract_session_field("No goal here", "Goal") is None
    assert RepoStatusNormalizer._extract_session_field(None, "Goal") is None


def test_extract_emphasized_value_basic():
    text = "**Current Stage:** Backend MVP"
    assert (
        RepoStatusNormalizer._extract_emphasized_value(text, "Current Stage")
        == "Backend MVP"
    )


def test_extract_emphasized_value_returns_none():
    assert (
        RepoStatusNormalizer._extract_emphasized_value("No match here", "Phase") is None
    )
    assert RepoStatusNormalizer._extract_emphasized_value(None, "Phase") is None


def test_extract_first_action_item_bullet():
    text = "## Immediate Next Steps\n- Build the sync service\n- Add tests\n"
    assert (
        RepoStatusNormalizer._extract_first_action_item(text)
        == "Build the sync service"
    )


def test_extract_first_action_item_numbered():
    text = "## Next Steps\n1. Deploy to production\n2. Monitor logs\n"
    assert (
        RepoStatusNormalizer._extract_first_action_item(text) == "Deploy to production"
    )


def test_extract_first_action_item_no_section():
    text = "# README\n\nSome content without a next steps section.\n"
    assert RepoStatusNormalizer._extract_first_action_item(text) is None


def test_first_content_paragraph_skips_heading_and_metadata():
    # Metadata pattern requires colon OUTSIDE **: **Key**: value
    text = (
        "# Project Manager\n\n"
        "**Version**: 0.1.0\n**Status**: Active\n\n"
        "Internal dashboard for repo status.\n"
    )
    result = RepoStatusNormalizer._first_content_paragraph(text)
    assert result == "Internal dashboard for repo status."


def test_first_content_paragraph_returns_none_for_all_metadata():
    # All paragraphs are metadata-style (**Key**: value)
    text = "**Status**: Active\n**Version**: 1.0\n"
    assert RepoStatusNormalizer._first_content_paragraph(text) is None


def test_first_content_paragraph_returns_none_for_empty():
    assert RepoStatusNormalizer._first_content_paragraph(None) is None
    assert RepoStatusNormalizer._first_content_paragraph("") is None


def test_find_blocked_schedule_items_finds_warning_lines():
    text = (
        "| 7.4 | Stale alerts | AI | Alerts | ⚠ Risk/Blocked | Requires scheduling |\n"
    )
    result = RepoStatusNormalizer._find_blocked_schedule_items(text)
    assert len(result) == 1
    assert "⚠" in result[0]


def test_find_blocked_schedule_items_empty():
    assert RepoStatusNormalizer._find_blocked_schedule_items(None) == []
    assert RepoStatusNormalizer._find_blocked_schedule_items("No warnings here") == []


def test_extract_summary_paragraph_basic():
    text = "## Summary\n\nCompleted all planned phases.\n\n## Next Steps\n\nFoo.\n"
    assert (
        RepoStatusNormalizer._extract_summary_paragraph(text)
        == "Completed all planned phases."
    )


def test_extract_summary_paragraph_returns_none_when_absent():
    assert (
        RepoStatusNormalizer._extract_summary_paragraph("# No summary section") is None
    )
    assert RepoStatusNormalizer._extract_summary_paragraph(None) is None


def test_is_non_blocker_value_positive_cases():
    assert RepoStatusNormalizer._is_non_blocker_value("None") is True
    assert RepoStatusNormalizer._is_non_blocker_value("No blockers") is True
    assert RepoStatusNormalizer._is_non_blocker_value("N/A") is True
    assert RepoStatusNormalizer._is_non_blocker_value("none (all green)") is True


def test_is_non_blocker_value_negative_cases():
    assert RepoStatusNormalizer._is_non_blocker_value("CI pipeline is broken") is False
    assert RepoStatusNormalizer._is_non_blocker_value("Waiting on PR review") is False
