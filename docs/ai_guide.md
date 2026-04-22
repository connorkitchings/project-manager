# AI Guide

This is the shortest path for an AI agent or human collaborator to get productive in this repository.

## Read Order

1. `README.md`
2. `.agent/CONTEXT.md`
3. `docs/project_charter.md`
4. `docs/implementation_schedule.md`
5. `docs/runbook.md`
6. Latest file in `session_logs/`

## What This Repo Is

Project Manager is an internal web app for reviewing the status of selected GitHub repositories. The app should read project documentation directly from tracked repos and supplement that with recent GitHub activity.

## Core Working Rules

- Never work on `main`
- Start and end sessions deliberately
- Update docs when assumptions change
- Treat repository documentation as product data
- Keep implementation choices simple until the status model is proven

## Typical Workflows

### Product or Architecture Change

1. Read the charter and current schedule.
2. Update the relevant docs first.
3. Capture any new decision in the charter or ADRs.
4. Only then make implementation changes.

### Parser or Integration Work

1. Identify the exact repo files and GitHub signals being consumed.
2. Define the expected normalized output.
3. Add tests around the normalization logic.
4. Document any fallback behavior in the charter, runbook, or knowledge base.

### UI Work

1. Confirm the dashboard view or detail view behavior against the charter.
2. Keep v1 narrow: single-user internal workflow, curated repo list, clear summaries.
3. Update docs if UI language changes the status model or user expectations.

## Fast Commands

```bash
git checkout -b feat/<topic>
uv sync
uv run ruff format .
uv run ruff check .
uv run pytest
uv run mkdocs build
```

## Current Non-Goals

- Org-wide repo discovery
- Multi-user permissions
- Full write-back workflows into GitHub or tracked repos
- Broad analytics unrelated to repo status review

## Handoff Expectations

- Write a session log
- Link changes to the schedule when relevant
- Call out any remaining template-era code or docs that could confuse the next session
