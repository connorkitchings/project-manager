# Context Router (Project Manager)

> Routing hub for the repository. Use this page to orient quickly, then jump to the right source of truth.

## Current Project Identity

- **Project:** Project Manager
- **Goal:** Build a simple internal web app for reviewing the status of selected GitHub repositories.
- **Primary inputs:** repository documentation plus recent GitHub activity
- **Current phase:** full-stack MVP with React frontend and persisted backend state

## Read Order

1. `README.md` - Product overview and current state
2. `docs/project_charter.md` - Scope, architecture, and assumptions
3. `docs/implementation_schedule.md` - Active roadmap
4. `.agent/skills/CATALOG.md` - Available workflows
5. Latest file in `session_logs/` - Most recent work context

## Repo Map

```text
project-manager/
├── .agent/              # Agent instructions, workflows, dynamic memory
├── .codex/              # Quick references for terminal-based agents
├── config/              # tracked_repos.yaml (YAML bootstrap registry)
├── docs/                # Product, architecture, and operating documentation
├── scripts/             # Utility scripts (vibe_sync.py session management)
├── src/project_manager/ # Flask backend (api, core, services, utils, models)
├── tests/               # Test suite (pytest, 74% coverage)
├── ui/                  # React/Vite/Tailwind frontend
└── session_logs/        # Session history
```

## Current Truths

- The repository began as a generic template, but the active backend now lives under `src/project_manager/`.
- The frontend lives under `ui/` and is built into assets served by Flask.
- The product direction is now fixed around a documentation-aware GitHub repo status dashboard.
- v1 is a single-user internal web app with a curated repo list.
- Repository docs provide intent; GitHub activity provides corroborating evidence and freshness.
- Tracked repos bootstrap from `config/tracked_repos.yaml`, and latest snapshots persist in SQLite.

## Immediate Focus

- Keep docs aligned with the combined Flask + React application that now exists.
- Tighten the normalized repo status model and stale/attention rules.
- Expand tracked repo management beyond the seed YAML file.

## Post-Session Protocol

Before ending a session:

1. Review what changed and whether a new pattern should be captured.
2. Update `.agent/PLAYBOOK.md` if a rule or reusable strategy emerged.
3. Write a session log in `session_logs/`.
