# Getting Started

This guide is for contributors working on Project Manager itself, not for consumers of the original template.

## What You Are Working On

Project Manager is an internal web application for reviewing the status of selected GitHub repositories. The product relies on a consistent set of docs inside each tracked repo and supplements that information with recent GitHub activity.

The codebase still contains template-era scaffolding and names such as `vibe_coding`. Treat those as migration debt, not product truth.

## Prerequisites

- Python 3.10+
- `uv`
- Git

## Initial Setup

```bash
uv sync
git checkout -b feat/<topic>
uv run pytest
uv run mkdocs build
```

## Read Before You Change Anything

1. `README.md`
2. `.agent/CONTEXT.md`
3. `docs/project_charter.md`
4. `docs/implementation_schedule.md`
5. `.agent/skills/start-session/SKILL.md`

## First-Day Workflow

1. Confirm you are not on `main`.
2. Review the charter and schedule to understand the current phase.
3. Check the latest file in `session_logs/`.
4. Decide whether your task changes product behavior, status parsing, or only documentation.
5. Update docs whenever a product or architecture assumption changes.

## Useful Commands

```bash
git status
uv run ruff format .
uv run ruff check .
uv run pytest -q
mkdocs serve
```

## What To Keep In Mind

- The dashboard is single-user and internal in v1.
- A curated repo list is the only supported inclusion model in v1.
- Repository docs are the primary input; GitHub activity is secondary evidence.
- If a doc and code path disagree, update the doc or record the mismatch explicitly.

## Verification

Before handing off work:

- Run the smallest relevant test scope.
- Build the docs site if you changed docs.
- Record the session in `session_logs/`.
