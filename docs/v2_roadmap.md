# v2 Roadmap

This document captures next-phase product decisions for Project Manager following the v1 MVP.

**Status:** Draft — open for prioritization  
**Last updated:** 2026-04-22  
**v1 reference:** `docs/implementation_schedule.md` (Phases 1-6)

---

## v1 Recap

The v1 MVP delivered:
- Dashboard of tracked repos with filterable status cards
- Repo detail view (goal, milestone, updates, blockers, docs sources, GitHub activity)
- Tracked repo management UI (add, enable/disable)
- SQLite-backed persistence (YAML bootstraps; SQLite is runtime source of truth)
- On-demand sync via `POST /api/sync`
- Normalized status model from repo docs + GitHub activity

What v1 intentionally deferred:

> "Out of scope for v1: org-wide discovery, multi-user permissions, writing back to repos, portfolio analytics."

---

## v2 Candidate Features

### 1. Delete / Archive Tracked Repos

**Problem:** There is no way to remove a tracked repo from the dashboard. Users can disable (hide from dashboard) but the repo stays in the database forever.

**Proposed behavior:**
- `DELETE /api/tracked-repos/<id>` endpoint with a soft-delete or hard-delete option
- Soft-delete: mark `archived=true`, hide from dashboard and settings by default, recoverable
- Hard-delete: purge snapshots and sync history along with the repo record
- UI: add a "Remove" action to the settings page with a confirmation step

**Effort:** S  
**Risk:** Low — additive endpoint, no impact on enabled repos

---

### 2. Stale / Attention Alerts

**Problem:** The dashboard surfaces attention states (missing docs, stale data) reactively — only after a sync. There is no proactive alerting when a repo goes stale.

**Proposed behavior:**
- Background sync on a configurable schedule (e.g., every 6 hours)
- `stale_after_days` threshold already exists in `Settings`; surface this more prominently
- Optional desktop notification or webhook when a repo transitions to `attention` status
- Dashboard badge showing when the last sync occurred and how many repos are stale

**Effort:** M  
**Risk:** Medium — background scheduling introduces a new runtime component

---

### 3. GitHub Repository Discovery

**Problem:** Adding a new repo requires knowing the exact `owner/repo` string. There is no search or browse experience.

**Proposed behavior:**
- Search GitHub repos by name/topic/org within the settings UI
- Filter to repos that match the expected documentation structure (have `README.md`, `docs/project_charter.md`, etc.)
- One-click "Add to dashboard" from search results
- Option to list all repos for a configured GitHub user/org

**Effort:** L  
**Risk:** Medium — requires GitHub search API scope, rate limit management

---

### 4. Generated Summary Artifacts

**Problem:** Status summaries are parsed deterministically from structured docs. This works well for repos following the template but degrades when docs are sparse or inconsistent.

**Proposed behavior:**
- Optional AI-generated summary per repo using an LLM (e.g., Claude API)
- Summaries cached alongside the snapshot; regenerated on sync
- Show generated summary alongside parsed fields in the detail view
- Flag generated vs. parsed content clearly in the UI

**Effort:** M  
**Risk:** Medium — external API cost, latency, and quality variance

---

### 5. Timeline View

**Problem:** The current detail view shows updates and GitHub events separately. There is no unified chronological view of what happened.

**Proposed behavior:**
- Merged timeline on the repo detail page: session log entries, commits, PRs, issues — sorted by date
- Filter by type (docs-only, GitHub-only, all)
- Optional date range picker

**Effort:** M  
**Risk:** Low — frontend-only, data already available

---

### 6. Richer Status Field Contract

**Problem:** The `RepoSummary` / `RepoDetail` schema was designed small for v1. Some fields are loosely defined (e.g., `summary` and `status_summary` overlap; `notes` is free-text).

**Open questions:**
- Which fields are mandatory vs. optional?
- Should `status` be a typed enum (healthy / active / stalled / blocked / unknown)?
- How should the app merge GitHub events with session logs — currently they are separate lists
- Should blockers be a structured list or free text?

**Proposed work:**
- Define a formal `RepoStatus` enum in `models.py`
- Tighten the OpenAPI schema to mark required vs. optional fields
- Update the normalizer to produce typed status values
- Update the frontend to render status badges by enum value rather than string matching

**Effort:** M  
**Risk:** Medium — requires coordinated backend + frontend + API doc changes

---

## Suggested Prioritization

| Priority | Feature | Rationale |
|----------|---------|-----------|
| 1 | Delete/Archive | Unblocks full lifecycle management; small effort |
| 2 | Richer Status Contract | Foundational — clarifies the model before building on top of it |
| 3 | Timeline View | High visibility, low risk, all data already exists |
| 4 | Stale/Attention Alerts | Adds proactive value once status model is solid |
| 5 | Discovery | Useful but not urgent while repo count is small |
| 6 | Generated Summaries | Highest complexity and cost; defer until parsing quality ceiling is hit |

---

## Open Questions

- Should delete be soft (archive) or hard (purge)? Hard delete is simpler but loses history.
- Is scheduled background sync worth the added complexity, or is manual sync sufficient for v1 usage patterns?
- What is the right status taxonomy? Healthy / Active / Stalled / Blocked / Unknown seems workable.
- Should generated summaries require an opt-in token config, or should they be off by default?
