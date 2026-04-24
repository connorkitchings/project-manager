# Session Log — 2026-04-22 (Session 1)

## TL;DR (≤5 lines)
- **Goal**: Clean up accumulated repo debt, fix inaccuracies, tighten CI, trim scaffolding, capture v2 direction
- **Accomplished**: All 6 phases completed — 7 commits, clean branch, ready for merge
- **Blockers**: None
- **Next**: Phase 7.1 — `DELETE /api/tracked-repos/<id>` + archive UI (suggested first, small effort)
- **Branch**: `docs/github-repo-status-docs`

**Tags**: ["chore", "docs", "cleanup", "ci", "roadmap"]

---

## Context
- **Started**: ~session start
- **Ended**: ~session end
- **Duration**: ~1 session
- **User Request**: Learn about the project, determine how to improve/clean up the repo, determine what's next

---

## Work Completed

### Phase 1: Commit Accumulated Work (4 commits)

Previously ~60+ unstaged changes and ~40 file deletions had never been committed (only 1 initial commit existed on `main`).

- `dcf3ddd` — Replaced `src/vibe_coding/` template with `src/project_manager/`, `ui/`, `config/`
- `9bb658d` — Removed 6 dead template scripts
- `aa4fc9a` — Replaced 15+ template tests with real test suite (70 tests, 74% coverage)
- `a7b58dd` — Updated all docs, CI, Makefile, pyproject.toml, gitignore

### Phase 2: Fix Documentation Inaccuracies

- `docs/getting_started.md` — Added Node.js prereq, frontend commands (`npm --prefix ui install/dev/build/test`), fixed `mkdocs serve` → `uv run mkdocs serve`, removed stale vibe_coding reference
- `docs/project_charter.md` — Fixed "Python 3.14" → "Python 3.10–3.12"
- `docs/implementation_schedule.md` — Marked Phase 2.1 Done (status schema is fully implemented)
- `.agent/CONTEXT.md` — Added `ui/` and `config/` to repo map

### Phase 3: CI Improvements

- `f6a7ed9` — Added `ruff format --check .` enforcement, added `npx tsc --noEmit` to frontend job, removed `|| true` from bandit, renamed "Validate Template" → "Build Docs", removed the dead `type-check` job (mypy not installed)

### Phase 4: Code Quality Fixes

- `src/project_manager/utils/markdown_fetcher.py` — Fixed User-Agent from `VibeCoding/1.0` to `ProjectManager/1.0` with correct GitHub URL
- `scripts/check_links.py` — Fixed `ROOT / "documents"` (nonexistent) → `ROOT / "docs"`
- `pyproject.toml` — Removed duplicate `[project.optional-dependencies].dev`, moved `typer`/`rich`/`pyperclip` from production deps to dev group (scripts-only deps)
- Applied `ruff format` to 5 files that were out of compliance
- Moved GitHub issue templates from `config/github/ISSUE_TEMPLATE/` to `.github/ISSUE_TEMPLATE/` (so GitHub picks them up), removed `config/github/` directory

### Phase 5: Trim Agent Scaffolding

- `34a90eb` — Removed `VIBE_CODING.md` (6KB) and `VIBE_CRITIQUE_PROMPTS.md` (25KB) — template-era reference material
- Removed 4 unused generic skills: `data-ingestion`, `database-migration`, `mcp-workflow`, `web-init`
- Updated `CATALOG.md`, `PLAYBOOK.md`, `AGENTS.md` to remove references to deleted files
- Trimmed `.gitignore` of irrelevant tool sections (Django, Scrapy, SageMath, Marimo, Pixi, Abstra, etc.)

### Phase 6: v2 Roadmap

- `9cfadef` — Created `docs/v2_roadmap.md` with 6 prioritized feature candidates
- Updated `docs/implementation_schedule.md`: Phase 6.3 → Done, added Phase 7 table
- Added `v2_roadmap.md` to MkDocs nav

### Files Modified (key)
- `.agent/AGENTS.md` — Removed deleted skill references
- `.agent/CONTEXT.md` — Repo map updated
- `.agent/PLAYBOOK.md` — Removed VIBE_CRITIQUE_PROMPTS reference
- `.agent/skills/CATALOG.md` — Removed 4 deleted skills
- `.github/workflows/ci.yml` — Tightened enforcement
- `.gitignore` — Trimmed to relevant tools only
- `docs/getting_started.md` — Node.js prereq + frontend commands
- `docs/implementation_schedule.md` — Phase 2.1 + 6.3 Done, Phase 7 added
- `docs/project_charter.md` — Python version fix
- `docs/v2_roadmap.md` — Created
- `pyproject.toml` — Dep cleanup
- `scripts/check_links.py` — Path fix
- `src/project_manager/utils/markdown_fetcher.py` — User-Agent fix

### Commands Run
```bash
uv run pytest -q                     # 70 passed, 74% coverage
uv run ruff check .                  # All checks passed
uv run ruff format --check .         # 35 files clean
uv sync                              # Lockfile updated after dep changes
```

---

## Decisions Made

- **Kept bandit with enforcement** (removed `|| true`) since it can be run cleanly on Python 3.10 in CI even if pydantic-core build fails on local Python 3.14
- **Removed mypy job entirely** rather than keeping a no-op — mypy isn't in project deps and was never enforced; add it back if/when type checking is adopted
- **Soft-removed VIBE_CODING.md** — key principles from that doc are already captured in PLAYBOOK.md Rules 6-9
- **Moved GitHub templates rather than deleting** — they're generic but correct and worth having in `.github/ISSUE_TEMPLATE/`
- **Left `_serialize_datetime` duplication** in `models.py` and `storage.py` — they serve different contexts (API JSON vs SQLite storage) and consolidating would create bad coupling

---

## Issues Encountered

- `bandit --extra security` fails locally on Python 3.14 due to pydantic-core requiring Rust compilation; works fine on Python 3.10 in CI — no action needed
- `ruff format --check` found 5 files out of compliance (`api/main.py`, `core/settings.py`, `services/normalizer.py`, `services/sync.py`, `tests/services/test_normalizer.py`) — auto-fixed before adding CI enforcement

---

## Next Steps

1. **Phase 7.1**: Add `DELETE /api/tracked-repos/<id>` endpoint (soft-delete preferred) + "Remove" UI in settings page — small effort, completes the lifecycle
2. **Phase 7.2**: Discuss and finalize `RepoStatus` enum contract before implementing — foundational for everything that builds on the status model
3. **Phase 7.3**: Merged timeline view on repo detail page — all data already exists, frontend-only work

---

## Handoff Notes
- **Current state**: Branch `docs/github-repo-status-docs` has 7 clean commits, all tests passing, working tree clean. Ready to merge to `main` at any point.
- **Next priority**: Phase 7.1 (delete/archive) — see `docs/v2_roadmap.md` for full spec
- **Open question**: Soft-delete (archive flag) vs hard-delete (purge snapshots)? See v2 roadmap for trade-offs.
- **Context needed**: The full schema lives in `src/project_manager/models.py`; the storage layer is `services/storage.py`; the API routes are `api/main.py`

---

**Session Owner**: Claude Code (claude-sonnet-4-6)
**User**: connorkitchings
