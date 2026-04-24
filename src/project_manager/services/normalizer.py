"""Normalization logic for repo docs and GitHub activity."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from project_manager.core.settings import Settings
from project_manager.models import (
    GitHubActivity,
    RepoDetail,
    RepoDocumentBundle,
    TrackedRepo,
)


class RepoStatusNormalizer:
    """Build normalized repo status snapshots from raw inputs."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_unsynced_snapshot(self, repo: TrackedRepo) -> RepoDetail:
        """Return a placeholder snapshot for an unsynced repo."""
        return RepoDetail(
            id=repo.id,
            name=repo.display_name,
            full_name=repo.full_name,
            notes=repo.notes,
            status_summary="Not synced yet.",
            missing_sources=["not_synced"],
            attention_flag=True,
            attention_reasons=["Not synced yet."],
        )

    def build_error_snapshot(
        self,
        repo: TrackedRepo,
        error: str,
        synced_at: datetime,
    ) -> RepoDetail:
        """Return a snapshot describing a sync failure."""
        return RepoDetail(
            id=repo.id,
            name=repo.display_name,
            full_name=repo.full_name,
            notes=repo.notes,
            status_summary="Repository sync failed.",
            attention_flag=True,
            attention_reasons=["Sync failed."],
            missing_sources=["sync_failed"],
            sync_error=error,
            last_synced_at=synced_at,
        )

    def normalize(
        self,
        repo: TrackedRepo,
        docs: RepoDocumentBundle,
        activity: GitHubActivity,
        synced_at: datetime,
    ) -> RepoDetail:
        """Normalize repository docs and GitHub activity into one snapshot."""
        current_goal = (
            self._extract_session_field(docs.latest_session_log, "Goal")
            or self._extract_emphasized_value(docs.project_charter, "Technical Goal")
            or self._extract_first_action_item(docs.implementation_schedule)
        )
        status_summary = (
            self._first_content_paragraph(docs.readme)
            or self._extract_emphasized_value(docs.project_charter, "Vision")
            or self._extract_summary_paragraph(docs.latest_session_log)
            or "No project summary available."
        )
        milestone = (
            self._extract_emphasized_value(
                docs.implementation_schedule,
                "Next Milestone",
            )
            or self._extract_emphasized_value(
                docs.implementation_schedule, "Current Stage"
            )
            or self._extract_emphasized_value(docs.implementation_schedule, "Phase")
        )

        blockers = []
        blocker_text = self._extract_session_field(docs.latest_session_log, "Blockers")
        if blocker_text and not self._is_non_blocker_value(blocker_text):
            blockers.append(blocker_text)
        blockers.extend(self._find_blocked_schedule_items(docs.implementation_schedule))

        recent_updates = []
        accomplished = self._extract_session_field(
            docs.latest_session_log,
            "Accomplished",
        )
        if not accomplished:
            accomplished = self._extract_summary_paragraph(docs.latest_session_log)
        if accomplished and not self._is_non_blocker_value(accomplished):
            recent_updates.append(accomplished)

        for event in activity.flattened()[:3]:
            recent_updates.append(
                f"{event.type.replace('_', ' ').title()}: {event.title}"
            )

        missing_sources = list(docs.missing_sources)
        stale_cutoff = datetime.now(timezone.utc) - timedelta(
            days=self.settings.stale_after_days
        )
        is_stale = (
            activity.last_activity_at is None
            or activity.last_activity_at < stale_cutoff
        )

        attention_reasons = []
        if missing_sources:
            attention_reasons.append(f"Missing docs: {', '.join(missing_sources)}")
        if blockers:
            attention_reasons.append("Blockers recorded in project docs.")
        if not current_goal:
            attention_reasons.append("Current goal is unclear from the available docs.")
        if is_stale:
            attention_reasons.append(
                "No recent GitHub activity in the last "
                f"{self.settings.stale_after_days} days."
            )

        attention_flag = bool(attention_reasons)

        return RepoDetail(
            id=repo.id,
            name=repo.display_name,
            full_name=repo.full_name,
            notes=repo.notes,
            current_goal=current_goal,
            status_summary=status_summary,
            milestone=milestone,
            last_activity_at=activity.last_activity_at,
            attention_flag=attention_flag,
            attention_reasons=attention_reasons,
            missing_sources=missing_sources,
            last_synced_at=synced_at,
            recent_updates=recent_updates,
            blockers=blockers,
            github_activity=activity.flattened()[: self.settings.recent_activity_limit],
            documentation_sources=docs.documentation_sources,
        )

    @staticmethod
    def _extract_session_field(text: str | None, label: str) -> str | None:
        """Extract a markdown bold field from a session log."""
        if not text:
            return None
        pattern = (
            rf"(?:^|\n)\s*(?:-\s*)?"
            rf"\*\*{re.escape(label)}(?::)?\*\*(?::)?\s*(.+)"
        )
        match = re.search(pattern, text)
        if not match:
            return None
        return match.group(1).strip().rstrip(".")

    @staticmethod
    def _extract_emphasized_value(text: str | None, label: str) -> str | None:
        """Extract a markdown bold label value such as **Current Stage:**."""
        if not text:
            return None
        pattern = rf"\*\*{re.escape(label)}:\*\*\s*(.+)"
        match = re.search(pattern, text)
        return match.group(1).strip() if match else None

    @staticmethod
    def _extract_first_action_item(text: str | None) -> str | None:
        """Extract the first bullet or numbered item under immediate next steps."""
        if not text:
            return None

        lines = text.splitlines()
        in_section = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## "):
                in_section = stripped.lower() in {
                    "## immediate next steps",
                    "## next steps",
                }
                continue
            if not in_section:
                continue
            bullet_match = re.match(r"[-*]\s+(.*)", stripped)
            number_match = re.match(r"\d+\.\s+(.*)", stripped)
            if bullet_match:
                return bullet_match.group(1).strip()
            if number_match:
                return number_match.group(1).strip()
        return None

    @staticmethod
    def _first_content_paragraph(text: str | None) -> str | None:
        """Return the first substantive paragraph from markdown text."""
        if not text:
            return None

        paragraphs = [paragraph.strip() for paragraph in text.split("\n\n")]
        for paragraph in paragraphs:
            if not paragraph:
                continue
            if paragraph.startswith(("#", ">", "```", "|", "---")):
                continue
            lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
            if not lines:
                continue
            if all(line.startswith("![") for line in lines):
                continue
            if all(re.match(r"\*\*[^*]+\*\*:\s*", line) for line in lines):
                continue
            return " ".join(line.strip() for line in paragraph.splitlines())
        return None

    @staticmethod
    def _find_blocked_schedule_items(text: str | None) -> list[str]:
        """Collect blocked schedule rows or lines."""
        if not text:
            return []
        blocked_lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("**Status Legend:**"):
                continue
            if "⚠" in stripped:
                blocked_lines.append(line.strip("| ").strip())
        return blocked_lines

    @staticmethod
    def _extract_summary_paragraph(text: str | None) -> str | None:
        """Extract the first paragraph under a markdown summary heading."""
        if not text:
            return None

        lines = text.splitlines()
        in_summary = False
        collected: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## "):
                if in_summary:
                    break
                in_summary = stripped.lower() == "## summary"
                continue
            if not in_summary:
                continue
            if not stripped:
                if collected:
                    break
                continue
            if stripped.startswith("#"):
                break
            collected.append(stripped)

        if not collected:
            return None
        return " ".join(collected)

    @staticmethod
    def _is_non_blocker_value(value: str) -> bool:
        """Return whether a parsed field indicates no blockers/updates."""
        normalized = value.strip().lower()
        return normalized.startswith(("none", "no blockers", "n/a"))
