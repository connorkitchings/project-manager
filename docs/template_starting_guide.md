# Repository Transition Guide

This file keeps its legacy path for compatibility, but it now documents the remaining transition from the original template into Project Manager.

## Why This Exists

The repository still contains template-era names, examples, and scaffolding. Use this guide when cleaning up those leftovers so the implementation catches up with the new product docs.

## Remaining Transition Work

- Rename template-era package and module names such as `vibe_coding`
- Remove or replace data-science and ML placeholders that are no longer relevant
- Replace example API endpoints and stub scripts with Project Manager behavior
- Align tests with the real repo-status workflow

## Source-of-Truth Docs During Transition

Until the codebase is fully renamed, these documents define the real product:

- `README.md`
- `.agent/CONTEXT.md`
- `docs/project_charter.md`
- `docs/implementation_schedule.md`

If an older template artifact disagrees with those files, treat the artifact as migration debt.

## Suggested Cleanup Order

1. Finalize the normalized repo status model.
2. Replace template-era code paths with product-specific modules.
3. Remove obsolete docs, tests, and examples.
4. Update the project map and quick references once the structure stabilizes.
