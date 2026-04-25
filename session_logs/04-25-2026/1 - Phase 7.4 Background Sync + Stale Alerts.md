# Session Log — 2026-04-25 (Session 1)

## TL;DR (≤5 lines)
- **Goal**: Implement Phase 7.4 — Background sync + stale/attention alerts
- **Accomplished**: Full Phase 7.4 implementation — APScheduler-based background sync, data staleness detection, frontend stale data filter + warnings, toast notification system
- **Blockers**: None
- **Next**: Merge `feat/v2-background-sync-alerts` to `main`, then begin Phase 7.5 (GitHub discovery) or Docker deployment
- **Branch**: `feat/v2-background-sync-alerts`

**Tags**: ["feature", "backend", "frontend", "testing", "docs"]

---

## Context
- **Started**: ~11:00
- **Ended**: ~11:15
- **Duration**: ~1 session
- **User Request**: "Continue development. Consider current status vs final desired state and develop a plan."

## Work Completed

### Step 0: Housekeeping
- Merged `feat/v2-enum-timeline-tests` into `main` (fast-forward, 16 commits)
- Created `feat/v2-background-sync-alerts` branch from `main`

### Step 1: Backend — Sync Scheduling Infrastructure
- **`pyproject.toml`** — Added `apscheduler~=3.10` dependency
- **`src/project_manager/core/settings.py`** — Added `sync_interval_minutes` (default 360), `scheduler_enabled` (default true), `stale_data_threshold_hours` (default 48)
- **`src/project_manager/services/scheduler.py`** (NEW) — `SyncScheduler` class wrapping APScheduler's `BackgroundScheduler`; daemon thread; configurable interval; `start()`/`shutdown()`/`get_status()` lifecycle; `atexit` cleanup
- **`src/project_manager/services/storage.py`** — Added `get_stale_repo_ids(threshold_days)` query method
- **`src/project_manager/api/main.py`** — `create_app` now accepts optional `scheduler` parameter; scheduler started at app creation; `GET /api/meta` extended with `scheduler` object
- **`src/project_manager/api/dependencies.py`** — Added `get_sync_scheduler()` factory; wired `stale_data_threshold_hours` to sync service
- **`tests/services/test_scheduler.py`** (NEW, 8 tests) — Scheduler start/stop/status, disabled mode, sync error handling
- **`tests/services/test_storage.py`** (EXTENDED, +4 tests) — `get_stale_repo_ids` with fresh/old/disabled/unset scenarios
- **`tests/api/test_repos.py`** (EXTENDED) — Added `FakeScheduler` stub; all `create_app` calls updated; meta endpoint test verifies `scheduler` field

### Step 2: Backend — Data Staleness Detection
- **`src/project_manager/models.py`** — Added `is_data_stale: bool = False` to `RepoSummary`; propagated through `to_dict()` and `to_summary()`
- **`src/project_manager/services/sync.py`** — Added `stale_data_threshold_hours` parameter; `_is_snapshot_data_stale()` method; `get_repo_detail()` annotates snapshots with staleness
- **`tests/test_models.py`** (EXTENDED) — `is_data_stale` serialization and propagation tests
- **`tests/services/test_sync.py`** (EXTENDED, +3 tests) — Fresh data not stale, old data stale, unsynced repos

### Step 3: Frontend — Staleness Indicators
- **`ui/src/lib/api/types.ts`** — Added `SchedulerStatus` interface; `scheduler` to `RootResponse`; `is_data_stale` to `RepoSummary`
- **`ui/src/features/repos/ui.tsx`** — Added `"stale"` to `DashboardFilter` type; "Stale data" filter button; stale data warning on `RepoCard`; scheduler info in `PageBanner`
- **`ui/src/features/repos/dashboard-page.tsx`** — Added `stale` filter logic
- **`ui/src/features/repos/hooks.ts`** — Added `refetchInterval: 60_000ms` to `useMeta` and `useRepos` for auto-refresh

### Step 4: Frontend — Sync Result Notifications
- **`ui/src/features/repos/notifications.tsx`** (NEW) — `ToastProvider` context; `SyncNotificationWatcher` detects new background sync runs via polling; `ToastContainer` renders dismissable toasts with auto-dismiss (5s); supports success/warning/error variants
- **`ui/src/app/App.tsx`** — Wrapped in `ToastProvider`; added `SyncNotificationWatcher`
- **`ui/src/app/shell.tsx`** — Added `ToastContainer` to app shell

### Step 5: Documentation
- **`docs/implementation_schedule.md`** — Phase 7.4 marked ✅ Done; "Immediate Next Steps" and "Open Questions" updated
- **`docs/api/openapi.yaml`** — Added `SchedulerStatus` schema; `scheduler` to `RootResponse`; `is_data_stale` to `RepoSummary`

### Files Modified
- `pyproject.toml` — Added apscheduler dep
- `uv.lock` — Lockfile update
- `src/project_manager/core/settings.py` — 3 new settings
- `src/project_manager/services/scheduler.py` (NEW)
- `src/project_manager/services/storage.py` — `get_stale_repo_ids`
- `src/project_manager/services/sync.py` — Data staleness computation
- `src/project_manager/models.py` — `is_data_stale` field
- `src/project_manager/api/main.py` — Scheduler integration
- `src/project_manager/api/dependencies.py` — Scheduler + threshold wiring
- `ui/src/lib/api/types.ts` — New types
- `ui/src/features/repos/ui.tsx` — Stale filter + warnings + scheduler banner
- `ui/src/features/repos/dashboard-page.tsx` — Stale filter
- `ui/src/features/repos/hooks.ts` — Polling interval
- `ui/src/features/repos/notifications.tsx` (NEW)
- `ui/src/app/App.tsx` — ToastProvider + watcher
- `ui/src/app/shell.tsx` — ToastContainer
- `docs/implementation_schedule.md` — Updated
- `docs/api/openapi.yaml` — Updated
- `tests/services/test_scheduler.py` (NEW)
- `tests/services/test_storage.py` (EXTENDED)
- `tests/services/test_sync.py` (EXTENDED)
- `tests/api/test_repos.py` (EXTENDED)
- `tests/test_models.py` (EXTENDED)
- `ui/src/features/repos/dashboard-page.test.tsx` (EXTENDED)
- `ui/src/features/repos/repo-detail-page.test.tsx` (EXTENDED)

### Commands Run
```bash
uv add apscheduler~=3.10
uv run pytest -q          # 160 passed
uv run ruff check .       # All checks passed
uv run ruff format --check .  # 39 files formatted
npm --prefix ui run build # OK
npm --prefix ui test      # 10 passed
```

## Decisions Made
- **APScheduler 3.x over Celery** — No external broker needed for single-process local Docker deployment; APScheduler runs in daemon thread
- **Compute `is_data_stale` at read time** rather than persisting — Derived value that changes continuously; avoids schema migration for a computed field
- **60-second polling interval** for frontend queries when scheduler is running — Balances freshness with unnecessary API load
- **Toast notifications detect background syncs** by comparing `latest_sync_run.finished_at` timestamps — No WebSocket/SSE needed

## Issues Encountered
- None — all tests and builds passed on first attempt after implementation

## Next Steps
1. Merge `feat/v2-background-sync-alerts` to `main`
2. Choose next focus: Phase 7.5 (GitHub discovery), Phase 7.6 (AI summaries), or local Docker deployment
3. Consider adding frontend vitest coverage for the notification system

## Handoff Notes
- **Current state**: All Phase 7.4 complete, 160 backend tests + 10 frontend tests passing, lint/format clean
- **Last file edited**: `docs/api/openapi.yaml`
- **Blockers**: None
- **Next priority**: Merge to `main`, then start Phase 7.5 or Docker deployment
- **Open questions**: Should scheduler interval be configurable at runtime via API? What is the right `stale_data_threshold_hours` default?
- **New env vars**: `PROJECT_MANAGER_SYNC_INTERVAL_MINUTES` (default 360), `PROJECT_MANAGER_SCHEDULER_ENABLED` (default true), `PROJECT_MANAGER_STALE_DATA_THRESHOLD_HOURS` (default 48)

---

**Session Owner**: OpenCode (glm-5.1)
**User**: Connor Kitchings
