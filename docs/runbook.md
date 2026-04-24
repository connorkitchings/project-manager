# Runbook

This runbook covers the current operating expectations for Project Manager while the product is still in its early internal phase.

## Monitoring Priorities

- **Documentation integrity:** The product depends on tracked repos exposing predictable docs. Broken or missing docs should be treated as product data issues.
- **GitHub access:** The sync flow depends on valid GitHub credentials and enough API quota.
- **Sync quality:** If parsed summaries look wrong, compare raw repo docs and GitHub activity before changing parser behavior.
- **Docs site health:** `mkdocs build` is the quickest check that the repository documentation is still coherent.

## Common Issues

### Issue: `uv sync` fails or dependencies are missing

**Symptoms**

- Environment creation fails
- Local commands cannot import project modules

**Resolution**

1. Confirm Python 3.10+ is installed.
2. Re-run `uv sync`.
3. If the environment is stale, recreate `.venv` and sync again.

### Issue: GitHub credentials are missing or invalid

**Symptoms**

- Sync requests fail with authentication errors
- API requests return 401 or 403 responses

**Resolution**

1. Check the configured GitHub token in the local environment.
2. Verify the token has access to the tracked repos.
3. Retry after confirming the token is loaded by the app or CLI.
4. If the error mentions rate limiting, treat a token as required for the current tracked-repo set.

### Issue: Repo summary is incomplete

**Symptoms**

- Current goal or recent updates are blank
- A repo appears stale even though it is active

**Resolution**

1. Check whether the tracked repo contains the expected files:
   `README.md`, `docs/project_charter.md`, `docs/implementation_schedule.md`, recent `session_logs/`.
2. Confirm the repo actually follows the expected structure.
3. If the docs exist but parse poorly, capture an example and update parser rules rather than hard-coding a repo-specific fix.

## Current Validation Set

- `connorkitchings/FRED` - full charter, schedule, and session-log coverage
- `connorkitchings/panicstats` - strong README + session log, but no charter/schedule pair
- `connorkitchings/JamBandNerd` - broad README surface with partial template-era metadata
- `connorkitchings/Vibe-Coding` - template-shaped repo for the full-doc happy path

### Issue: Documentation build fails

**Symptoms**

- `mkdocs build` fails
- Navigation or links are broken

**Resolution**

1. Run `uv run mkdocs build` locally.
2. Fix broken links or invalid nav entries in `mkdocs.yml`.
3. If a page is intentionally legacy, mark it clearly and remove it from front-door navigation if needed.

## Rollback Guidance

The project has no deployment runbook yet. For now:

- Keep changes small and branch-based.
- Revert documentation or parser changes with a standard git revert if a change makes the docs misleading.
- Capture any rollback-worthy incident in `session_logs/` and `docs/knowledge_base.md`.

## Escalation

- **Primary maintainer:** Connor Kitchings
- **Escalate when:** parser behavior is unclear, a required status field cannot be inferred safely, or a GitHub permission issue blocks development
