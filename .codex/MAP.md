# Project Map

> Quick structural orientation for Project Manager.

## Root Level

```text
project-manager/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── mkdocs.yml
├── .agent/
├── .codex/
├── docs/
├── src/
├── tests/
├── scripts/
└── session_logs/
```

## Where To Start

- `README.md` - Product overview
- `.agent/CONTEXT.md` - Current repo context
- `docs/project_charter.md` - Product and architecture
- `docs/implementation_schedule.md` - Current roadmap

## Important Notes

- The repository still contains template-era implementation scaffolding.
- Front-door docs reflect the real product direction; older template artifacts should be treated as migration debt.

## Main Areas

### `.agent/`

Agent workflow, playbook, and session-management material.

### `.codex/`

Terminal-oriented quick references.

### `docs/`

Product, architecture, operations, and migration documentation.

### `src/`

Current implementation scaffold. Some names still reflect the original template and will be replaced later.

### `tests/`

Test suite, also partly inherited from the original template.

### `session_logs/`

Human and agent session continuity.
