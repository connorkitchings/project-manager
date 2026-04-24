# Quick Start

> Essential commands for working on Project Manager.

## Setup

```bash
uv sync
source .venv/bin/activate
```

## Daily Development

```bash
git branch
git checkout -b feat/<topic>
uv run ruff format .
uv run ruff check .
uv run pytest
mkdocs serve
```

## Documentation Flow

```bash
sed -n '1,200p' .agent/CONTEXT.md
sed -n '1,240p' docs/project_charter.md
sed -n '1,240p' docs/implementation_schedule.md
```

## Common Checks

```bash
uv run pytest -q
uv run pytest -vv
uv run mkdocs build
git status
```

## Working Assumptions

- Never work on `main`
- Session logs are required
- Docs are part of the product, not secondary artifacts
- The code scaffold still includes template-era names and may not match the final package structure yet

## Essential Files

- `README.md`
- `.agent/CONTEXT.md`
- `docs/project_charter.md`
- `docs/implementation_schedule.md`
- `.agent/skills/start-session/SKILL.md`
