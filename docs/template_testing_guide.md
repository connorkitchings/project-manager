# Validation Guide

This file keeps its legacy path for compatibility, but it now describes how to validate Project Manager while the repository is still mid-transition from the original template.

## Documentation Validation

```bash
uv run mkdocs build
rg -n "Vibe Coding|Data Science Template|Prefect|MLflow|OpenLineage" README.md docs .agent .codex
```

The goal is to keep front-door docs aligned with the actual product and catch leftover template references in active documentation.

## Development Validation

```bash
uv sync
uv run ruff format .
uv run ruff check .
uv run pytest
```

## Product-Fit Validation

Before implementation is considered on track, confirm:

- The charter still matches the intended product.
- The schedule reflects the next real milestone.
- The tracked repo status model is clearly defined.
- Remaining template artifacts are called out explicitly where they still exist.
