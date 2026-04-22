"""SQLite-backed persistence for tracked repos and repo snapshots."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from project_manager.models import GitHubEvent, RepoDetail, TrackedRepo

_UNSET = object()


class TrackedRepoExistsError(RuntimeError):
    """Raised when creating a tracked repo with a duplicate id."""


class TrackedRepoNotFoundError(KeyError):
    """Raised when a tracked repo id cannot be found."""


def _serialize_datetime(value: datetime | None) -> str | None:
    """Serialize a datetime to ISO 8601."""
    return value.isoformat() if value else None


def _deserialize_datetime(value: str | None) -> datetime | None:
    """Deserialize an ISO 8601 datetime string."""
    if not value:
        return None
    return datetime.fromisoformat(value)


class SQLiteAppStateStore:
    """Persist tracked repos, snapshots, and sync runs to SQLite."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self._lock = Lock()
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        """Create a new SQLite connection."""
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _connection(self):
        """Yield a SQLite connection and always close it."""
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _ensure_schema(self) -> None:
        """Create the database schema if it does not exist."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS tracked_repos (
                    id TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    repo TEXT NOT NULL,
                    name TEXT,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS repo_snapshots (
                    repo_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    current_goal TEXT,
                    status_summary TEXT,
                    milestone TEXT,
                    last_activity_at TEXT,
                    attention_flag INTEGER NOT NULL DEFAULT 0,
                    attention_reasons TEXT NOT NULL DEFAULT '[]',
                    missing_sources TEXT NOT NULL DEFAULT '[]',
                    last_synced_at TEXT,
                    sync_error TEXT,
                    notes TEXT,
                    recent_updates TEXT NOT NULL DEFAULT '[]',
                    blockers TEXT NOT NULL DEFAULT '[]',
                    github_activity TEXT NOT NULL DEFAULT '[]',
                    documentation_sources TEXT NOT NULL DEFAULT '[]',
                    FOREIGN KEY (repo_id) REFERENCES tracked_repos(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS sync_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    synced_count INTEGER NOT NULL,
                    failed_count INTEGER NOT NULL
                );
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(repo_snapshots)")
            }
            if "attention_reasons" not in columns:
                connection.execute(
                    """
                    ALTER TABLE repo_snapshots
                    ADD COLUMN attention_reasons TEXT NOT NULL DEFAULT '[]'
                    """
                )

    def bootstrap_tracked_repos(self, repos: list[TrackedRepo]) -> None:
        """Upsert tracked repos from YAML into SQLite."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connection() as connection:
            connection.executemany(
                """
                INSERT INTO tracked_repos (
                    id, owner, repo, name, enabled, notes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    owner = excluded.owner,
                    repo = excluded.repo,
                    name = COALESCE(tracked_repos.name, excluded.name),
                    enabled = tracked_repos.enabled,
                    notes = COALESCE(tracked_repos.notes, excluded.notes),
                    updated_at = excluded.updated_at
                """,
                [
                    (
                        repo.id,
                        repo.owner,
                        repo.repo,
                        repo.name,
                        1 if repo.enabled else 0,
                        repo.notes,
                        now,
                        now,
                    )
                    for repo in repos
                ],
            )

    def list_tracked_repos(self) -> list[TrackedRepo]:
        """List all tracked repos, including disabled ones."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, owner, repo, name, enabled, notes
                FROM tracked_repos
                ORDER BY id
                """
            ).fetchall()
        return [self._row_to_tracked_repo(row) for row in rows]

    def list_enabled_repos(self) -> list[TrackedRepo]:
        """List enabled tracked repos from SQLite."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, owner, repo, name, enabled, notes
                FROM tracked_repos
                WHERE enabled = 1
                ORDER BY id
                """
            ).fetchall()
        return [self._row_to_tracked_repo(row) for row in rows]

    def get_tracked_repo(
        self,
        repo_id: str,
        *,
        include_disabled: bool = False,
    ) -> TrackedRepo:
        """Get one tracked repo by id from SQLite."""
        query = """
            SELECT id, owner, repo, name, enabled, notes
            FROM tracked_repos
            WHERE id = ?
        """
        params = [repo_id]
        if not include_disabled:
            query += " AND enabled = 1"
        with self._connection() as connection:
            row = connection.execute(
                query,
                params,
            ).fetchone()
        if row is None:
            raise TrackedRepoNotFoundError(f"Tracked repo not found: {repo_id}")
        return self._row_to_tracked_repo(row)

    def create_tracked_repo(self, repo: TrackedRepo) -> TrackedRepo:
        """Create a new tracked repo in SQLite."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self._lock, self._connection() as connection:
                connection.execute(
                    """
                    INSERT INTO tracked_repos (
                        id, owner, repo, name, enabled, notes, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        repo.id,
                        repo.owner,
                        repo.repo,
                        repo.name,
                        1 if repo.enabled else 0,
                        repo.notes,
                        now,
                        now,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise TrackedRepoExistsError(
                f"Tracked repo id already exists: {repo.id}"
            ) from exc
        return self.get_tracked_repo(repo.id, include_disabled=True)

    def update_tracked_repo(
        self,
        repo_id: str,
        *,
        enabled: bool | object = _UNSET,
        name: str | None | object = _UNSET,
        notes: str | None | object = _UNSET,
    ) -> TrackedRepo:
        """Update runtime-managed fields for an existing tracked repo."""
        updates: list[str] = []
        params: list[object] = []
        if enabled is not _UNSET:
            updates.append("enabled = ?")
            params.append(1 if enabled else 0)
        if name is not _UNSET:
            updates.append("name = ?")
            params.append(name)
        if notes is not _UNSET:
            updates.append("notes = ?")
            params.append(notes)
        if not updates:
            return self.get_tracked_repo(repo_id, include_disabled=True)

        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(repo_id)

        with self._lock, self._connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE tracked_repos
                SET {", ".join(updates)}
                WHERE id = ?
                """,
                params,
            )
            if cursor.rowcount == 0:
                raise TrackedRepoNotFoundError(f"Tracked repo not found: {repo_id}")
        return self.get_tracked_repo(repo_id, include_disabled=True)

    def get_snapshot(self, repo_id: str) -> RepoDetail | None:
        """Return the latest snapshot for a repo if present."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM repo_snapshots WHERE repo_id = ?",
                (repo_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_snapshot(row)

    def upsert_snapshot(self, snapshot: RepoDetail) -> None:
        """Persist the latest snapshot for a repo."""
        github_activity = json.dumps(
            [event.to_dict() for event in snapshot.github_activity]
        )
        with self._lock, self._connection() as connection:
            connection.execute(
                """
                INSERT INTO repo_snapshots (
                    repo_id, name, full_name, current_goal, status_summary, milestone,
                    last_activity_at, attention_flag, attention_reasons,
                    missing_sources, last_synced_at, sync_error, notes,
                    recent_updates, blockers, github_activity,
                    documentation_sources
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(repo_id) DO UPDATE SET
                    name = excluded.name,
                    full_name = excluded.full_name,
                    current_goal = excluded.current_goal,
                    status_summary = excluded.status_summary,
                    milestone = excluded.milestone,
                    last_activity_at = excluded.last_activity_at,
                    attention_flag = excluded.attention_flag,
                    attention_reasons = excluded.attention_reasons,
                    missing_sources = excluded.missing_sources,
                    last_synced_at = excluded.last_synced_at,
                    sync_error = excluded.sync_error,
                    notes = excluded.notes,
                    recent_updates = excluded.recent_updates,
                    blockers = excluded.blockers,
                    github_activity = excluded.github_activity,
                    documentation_sources = excluded.documentation_sources
                """,
                (
                    snapshot.id,
                    snapshot.name,
                    snapshot.full_name,
                    snapshot.current_goal,
                    snapshot.status_summary,
                    snapshot.milestone,
                    _serialize_datetime(snapshot.last_activity_at),
                    1 if snapshot.attention_flag else 0,
                    json.dumps(snapshot.attention_reasons),
                    json.dumps(snapshot.missing_sources),
                    _serialize_datetime(snapshot.last_synced_at),
                    snapshot.sync_error,
                    snapshot.notes,
                    json.dumps(snapshot.recent_updates),
                    json.dumps(snapshot.blockers),
                    github_activity,
                    json.dumps(snapshot.documentation_sources),
                ),
            )

    def record_sync_run(
        self,
        *,
        started_at: datetime,
        finished_at: datetime,
        synced_count: int,
        failed_count: int,
    ) -> None:
        """Persist aggregate sync metadata."""
        with self._lock, self._connection() as connection:
            connection.execute(
                """
                INSERT INTO sync_runs (
                    started_at, finished_at, synced_count, failed_count
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    started_at.isoformat(),
                    finished_at.isoformat(),
                    synced_count,
                    failed_count,
                ),
            )

    def get_latest_sync_run(self) -> dict[str, object] | None:
        """Return the most recent sync run metadata."""
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT started_at, finished_at, synced_count, failed_count
                FROM sync_runs
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        return {
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "synced_count": row["synced_count"],
            "failed_count": row["failed_count"],
        }

    @staticmethod
    def _row_to_tracked_repo(row: sqlite3.Row) -> TrackedRepo:
        """Convert a tracked repo row to a dataclass."""
        return TrackedRepo(
            id=row["id"],
            owner=row["owner"],
            repo=row["repo"],
            name=row["name"],
            enabled=bool(row["enabled"]),
            notes=row["notes"],
        )

    @staticmethod
    def _row_to_snapshot(row: sqlite3.Row) -> RepoDetail:
        """Convert a snapshot row to a detailed repo snapshot."""
        github_activity = [
            GitHubEvent(
                type=event["type"],
                title=event["title"],
                url=event.get("url"),
                occurred_at=_deserialize_datetime(event.get("occurred_at")),
            )
            for event in json.loads(row["github_activity"])
        ]
        return RepoDetail(
            id=row["repo_id"],
            name=row["name"],
            full_name=row["full_name"],
            current_goal=row["current_goal"],
            status_summary=row["status_summary"],
            milestone=row["milestone"],
            last_activity_at=_deserialize_datetime(row["last_activity_at"]),
            attention_flag=bool(row["attention_flag"]),
            attention_reasons=json.loads(row["attention_reasons"]),
            missing_sources=json.loads(row["missing_sources"]),
            last_synced_at=_deserialize_datetime(row["last_synced_at"]),
            sync_error=row["sync_error"],
            notes=row["notes"],
            recent_updates=json.loads(row["recent_updates"]),
            blockers=json.loads(row["blockers"]),
            github_activity=github_activity,
            documentation_sources=json.loads(row["documentation_sources"]),
        )
