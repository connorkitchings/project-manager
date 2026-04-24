# Project Manager

> Internal web dashboard for reviewing the status of selected GitHub repositories.

## Overview

Project Manager is a documentation-aware portfolio dashboard for repositories built with this team's working template. It combines structured project docs with recent GitHub activity so one person can quickly answer:

- What is each project trying to do right now?
- What changed recently?
- Which repos are active, stalled, or unclear?
- Which repos should be included in the dashboard at all?

The product is intentionally narrow in v1:

- Single-user internal workflow
- Curated include/exclude list of repositories
- Web-first experience
- Repository docs as the primary source of intent
- GitHub activity as supporting evidence and freshness signals

## Current Status

This repository started from a generic AI/data-project template, but the active product now includes a Flask backend plus a built-in React frontend. The current MVP includes a dashboard, repo detail view, tracked-repo settings UI, YAML bootstrap registry, SQLite-backed app state, and on-demand sync for tracked repositories.

The default tracked-repo seed now validates the product against a small live set of public repos: `FRED`, `panicstats`, `JamBandNerd`, and `Vibe-Coding`.

## Planned v1 Capabilities

- Portfolio dashboard showing tracked repos and high-level health
- Easy repo inclusion and exclusion controls
- A normalized status snapshot per repo:
  current goal, recent updates, last activity, next milestone, and blockers when available
- Repo detail view combining parsed docs and recent GitHub signals
- Tracked repo management in the UI for adding repos and enabling/disabling them
- Lightweight sync flow that refreshes repo summaries on demand
- SQLite-backed persisted snapshots so sync results survive restarts

## Status Inputs

The first implementation should read directly from agreed repository documents plus GitHub metadata:

- `README.md`
- `docs/project_charter.md`
- `docs/implementation_schedule.md`
- recent `session_logs/`
- recent GitHub issues, pull requests, and commits

Over time, the project may add a canonical generated status artifact, but v1 should not require one.

## Quick Start

### Prerequisites

- Python 3.10+
- `uv`
- Git
- Node.js 20+
- GitHub token recommended for multi-repo sync

### Local Setup

```bash
uv sync
npm --prefix ui install
git checkout -b feat/<topic>
npm --prefix ui run build
uv run pytest -q
uv run --extra dev mkdocs serve
```

### Run The App

```bash
# Flask API
uv run flask --app project_manager.api.main run

# React dev server
npm --prefix ui run dev
```

### GitHub Sync Notes

- Configure `PROJECT_MANAGER_GITHUB_TOKEN` when using the seeded multi-repo validation set.
- Unauthenticated GitHub API access can hit rate limits quickly once the app syncs several repositories.
- New repos can be added from `/settings/repos`; the app validates that the GitHub repository exists before saving it into SQLite.

### Read First

- `.agent/CONTEXT.md`
- `docs/project_charter.md`
- `docs/implementation_schedule.md`
- `.agent/skills/start-session/SKILL.md`

## Documentation

- `docs/index.md` - Documentation hub
- `docs/project_brief.md` - Short product summary
- `docs/project_charter.md` - Product scope, architecture, and assumptions
- `docs/implementation_schedule.md` - Current roadmap
- `docs/runbook.md` - Operating notes and troubleshooting
- `docs/api/README.md` - Draft API direction

## Working Conventions

- Do not work directly on `main`
- Keep session logs in `session_logs/`
- Update docs when product direction changes
- Treat repository documentation as product data, not just prose

## Near-Term Priorities

1. Continue tightening the normalized repo status contract as new repo patterns appear.
2. Capture the first v2 roadmap decisions around alerts, discovery, and summary artifacts.
3. Decide whether tracked-repo management needs delete/archive behavior or broader GitHub discovery.

## Legacy Notes

Some low-level docs and code paths still reflect the original template. Where that remains true, the updated docs call it out explicitly instead of pretending the migration is complete.
