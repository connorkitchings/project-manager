"""Shared models for tracked repos, sync results, and API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Literal


class RepoStatus(str, Enum):
    """Typed health status for a tracked repository."""

    healthy = "healthy"
    active = "active"
    stalled = "stalled"
    blocked = "blocked"
    error = "error"
    unknown = "unknown"


def _serialize_datetime(value: datetime | None) -> str | None:
    """Serialize datetimes for JSON responses."""
    return value.isoformat() if value else None


@dataclass(slots=True)
class TrackedRepo:
    """Tracked repository registry entry."""

    id: str
    owner: str
    repo: str
    name: str | None = None
    enabled: bool = True
    notes: str | None = None

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"

    @property
    def display_name(self) -> str:
        return self.name or self.repo

    def to_dict(self) -> dict:
        """Serialize a tracked repo for API responses."""
        return {
            "id": self.id,
            "owner": self.owner,
            "repo": self.repo,
            "full_name": self.full_name,
            "name": self.name,
            "display_name": self.display_name,
            "enabled": self.enabled,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrackedRepo":
        """Build a tracked repo entry from registry data."""
        return cls(
            id=data["id"],
            owner=data["owner"],
            repo=data["repo"],
            name=data.get("name"),
            enabled=data.get("enabled", True),
            notes=data.get("notes"),
        )


@dataclass(slots=True)
class RepoDocumentBundle:
    """Raw repository docs collected during sync."""

    readme: str | None = None
    project_charter: str | None = None
    implementation_schedule: str | None = None
    latest_session_log: str | None = None
    documentation_sources: list[str] = field(default_factory=list)
    missing_sources: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GitHubEvent:
    """Single GitHub activity event."""

    type: Literal["commit", "pull_request", "issue"]
    title: str
    url: str | None = None
    occurred_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "title": self.title,
            "url": self.url,
            "occurred_at": _serialize_datetime(self.occurred_at),
        }


@dataclass(slots=True)
class GitHubActivity:
    """Recent GitHub activity grouped by type."""

    commits: list[GitHubEvent] = field(default_factory=list)
    pull_requests: list[GitHubEvent] = field(default_factory=list)
    issues: list[GitHubEvent] = field(default_factory=list)
    last_activity_at: datetime | None = None

    def flattened(self) -> list[GitHubEvent]:
        """Return all events sorted by timestamp descending."""
        events = self.commits + self.pull_requests + self.issues
        return sorted(
            events,
            key=lambda event: event.occurred_at
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )


@dataclass(slots=True)
class RepoSummary:
    """Summary representation of a tracked repository."""

    id: str
    name: str
    full_name: str
    current_goal: str | None = None
    status_summary: str | None = None
    milestone: str | None = None
    last_activity_at: datetime | None = None
    attention_flag: bool = False
    attention_reasons: list[str] = field(default_factory=list)
    missing_sources: list[str] = field(default_factory=list)
    last_synced_at: datetime | None = None
    sync_error: str | None = None
    status: RepoStatus = RepoStatus.unknown

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "full_name": self.full_name,
            "current_goal": self.current_goal,
            "status_summary": self.status_summary,
            "milestone": self.milestone,
            "last_activity_at": _serialize_datetime(self.last_activity_at),
            "attention_flag": self.attention_flag,
            "attention_reasons": self.attention_reasons,
            "missing_sources": self.missing_sources,
            "last_synced_at": _serialize_datetime(self.last_synced_at),
            "sync_error": self.sync_error,
            "status": self.status.value,
        }


@dataclass(slots=True)
class RepoDetail(RepoSummary):
    """Detailed representation of a tracked repository."""

    notes: str | None = None
    recent_updates: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    github_activity: list[GitHubEvent] = field(default_factory=list)
    documentation_sources: list[str] = field(default_factory=list)

    def to_summary(self) -> RepoSummary:
        """Return the summary-shaped version of this snapshot."""
        return RepoSummary(
            id=self.id,
            name=self.name,
            full_name=self.full_name,
            current_goal=self.current_goal,
            status_summary=self.status_summary,
            milestone=self.milestone,
            last_activity_at=self.last_activity_at,
            attention_flag=self.attention_flag,
            attention_reasons=list(self.attention_reasons),
            missing_sources=list(self.missing_sources),
            last_synced_at=self.last_synced_at,
            sync_error=self.sync_error,
            status=self.status,
        )

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update(
            {
                "notes": self.notes,
                "recent_updates": self.recent_updates,
                "blockers": self.blockers,
                "github_activity": [event.to_dict() for event in self.github_activity],
                "documentation_sources": self.documentation_sources,
            }
        )
        return data


@dataclass(slots=True)
class RepoListResponse:
    """List endpoint response."""

    repos: list[RepoSummary]

    def to_dict(self) -> dict:
        return {"repos": [repo.to_dict() for repo in self.repos]}


@dataclass(slots=True)
class TrackedRepoListResponse:
    """Tracked repo management list endpoint response."""

    tracked_repos: list[TrackedRepo]

    def to_dict(self) -> dict:
        return {"tracked_repos": [repo.to_dict() for repo in self.tracked_repos]}


@dataclass(slots=True)
class SyncResult:
    """Outcome for a single repo sync attempt."""

    repo_id: str
    synced: bool
    sync_error: str | None = None

    def to_dict(self) -> dict:
        return {
            "repo_id": self.repo_id,
            "synced": self.synced,
            "sync_error": self.sync_error,
        }


@dataclass(slots=True)
class SyncResponse:
    """Sync endpoint response."""

    results: list[SyncResult]
    synced_count: int

    def to_dict(self) -> dict:
        return {
            "results": [result.to_dict() for result in self.results],
            "synced_count": self.synced_count,
        }
