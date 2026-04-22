# Implementation Schedule

This schedule tracks the first productization work for Project Manager.

**Status Legend:** ☐ Not Started · ▶ In Progress · ✅ Done · ⚠ Risk/Blocked

## Overview

**Project:** Project Manager  
**Type:** Internal web application  
**Kickoff:** 2026-04-21  
**Current Stage:** full-stack MVP with persisted backend state

## Phase 1: Documentation Reset

| Phase | Task | Owner | Deliverable | Status | Notes |
|-------|------|-------|-------------|--------|-------|
| 1.1 | Replace template positioning in front-door docs | Connor + AI Assistant | README, charter, brief, docs index | ✅ Done | Core product docs now reflect Project Manager |
| 1.2 | Align agent context and quick references | Connor + AI Assistant | `.agent/CONTEXT.md`, `.codex/QUICKSTART.md`, AI guide | ✅ Done | Future sessions now route through the right product context |
| 1.3 | Mark or rewrite remaining migration docs | Connor + AI Assistant | transition and validation docs | ✅ Done | Legacy template references are now isolated as migration material |

## Phase 2: Repo Status Model

| Phase | Task | Owner | Deliverable | Status | Notes |
|-------|------|-------|-------------|--------|-------|
| 2.1 | Define normalized repo status fields | Connor | Draft schema / field contract | ✅ Done | Schema implemented in `models.py`, `docs/api/openapi.yaml`, and TypeScript types |
| 2.2 | Choose required source documents per tracked repo | Connor | Source-of-truth rules | ✅ Done | README, charter, schedule, session logs are the current parser targets |
| 2.3 | Define freshness and fallback behavior | Connor | Parser rules for missing or stale docs | ✅ Done | Missing docs and unsynced repos now surface as attention states |

## Phase 3: Sync and Parsing

| Phase | Task | Owner | Deliverable | Status | Notes |
|-------|------|-------|-------------|--------|-------|
| 3.1 | Build curated repo registry | AI Assistant | Config format for tracked repos | ✅ Done | `config/tracked_repos.yaml` is now the committed registry |
| 3.2 | Implement repository document reader | AI Assistant | Reader for standard project docs | ✅ Done | Reads README, charter, schedule, and latest session log via GitHub |
| 3.3 | Implement GitHub activity fetcher | AI Assistant | Recent commits, PRs, issues | ✅ Done | Supporting evidence, not source of truth |
| 3.4 | Normalize docs + GitHub into one snapshot | AI Assistant | Repo status snapshot model | ✅ Done | Unsynced and error states also normalize cleanly |
| 3.5 | Persist tracked repos and latest snapshots | AI Assistant | SQLite-backed app state | ✅ Done | YAML now bootstraps tracked repos into SQLite; sync state survives restarts |

## Phase 4: Dashboard MVP

| Phase | Task | Owner | Deliverable | Status | Notes |
|-------|------|-------|-------------|--------|-------|
| 4.1 | Build portfolio dashboard | AI Assistant | Repo list with filterable cards | ✅ Done | React SPA now renders tracked repo summaries with client-side filters |
| 4.2 | Build repo detail view | AI Assistant | Deep-dive page per repo | ✅ Done | Repo detail view now surfaces updates, blockers, docs, and GitHub activity |
| 4.3 | Add manual refresh or sync trigger | AI Assistant | Simple sync control | ✅ Done | `POST /api/sync` now triggers backend refresh |

## Phase 5: Runtime Repo Management

| Phase | Task | Owner | Deliverable | Status | Notes |
|-------|------|-------|-------------|--------|-------|
| 5.1 | Add tracked repo management endpoints | AI Assistant | Add/list/update API for tracked repos | ✅ Done | `GET/POST/PATCH /api/tracked-repos` now manage SQLite runtime state |
| 5.2 | Add tracked repo settings UI | AI Assistant | `/settings/repos` add + enable/disable flow | ✅ Done | New repos can be added without editing YAML; enable/disable updates dashboard coverage |
| 5.3 | Preserve YAML as bootstrap only | AI Assistant | Runtime state rules | ✅ Done | Startup seed still loads from YAML, but SQLite is the system of record after boot |

## Phase 6: Quality and Fit

| Phase | Task | Owner | Deliverable | Status | Notes |
|-------|------|-------|-------------|--------|-------|
| 6.1 | Validate against real repos | Connor + AI Assistant | Parser review across 3-5 repos | ✅ Done | Validation now covers FRED, PanicStats, JamBandNerd, and Vibe-Coding |
| 6.2 | Tighten UX copy and status language | Connor + AI Assistant | Consistent status taxonomy | ✅ Done | Attention states now expose explicit reasons in both API and UI |
| 6.3 | Capture v2 decisions | Connor | Follow-up roadmap | ✅ Done | See `docs/v2_roadmap.md` for prioritized feature candidates |

## Phase 7: v2 Development

See `docs/v2_roadmap.md` for full feature descriptions and prioritization rationale.

| Phase | Task | Owner | Deliverable | Status | Notes |
|-------|------|-------|-------------|--------|-------|
| 7.1 | Delete / Archive tracked repos | AI Assistant | `DELETE /api/tracked-repos/<id>` + UI | ☐ Not Started | Suggested first — small effort, completes lifecycle |
| 7.2 | Richer status field contract | Connor + AI Assistant | `RepoStatus` enum, tightened schema | ☐ Not Started | Foundational before building on top of the model |
| 7.3 | Timeline view | AI Assistant | Merged event timeline on repo detail page | ☐ Not Started | All data already exists; frontend-only |
| 7.4 | Stale / attention alerts | AI Assistant | Background sync + alert surface | ☐ Not Started | Requires scheduling; defer until status model is solid |
| 7.5 | GitHub repository discovery | AI Assistant | Search + one-click add UI | ☐ Not Started | GitHub search API integration |
| 7.6 | Generated summary artifacts | AI Assistant | LLM-based summaries via Claude API | ☐ Not Started | Highest complexity; defer until parsing ceiling is hit |

## Immediate Next Steps

1. Start Phase 7.1 (delete/archive) — small effort, completes the tracked repo lifecycle.
2. Discuss the `RepoStatus` enum contract before committing to Phase 7.2 changes.
3. Keep expanding parser coverage as new real repo patterns appear.

## Open Questions

- Should delete be soft (archive) or hard (purge)? See `docs/v2_roadmap.md`.
- What is the right status taxonomy? Healthy / Active / Stalled / Blocked / Unknown is the current candidate.
- Should background sync run on a schedule, or is manual-only sufficient for v1 usage patterns?
