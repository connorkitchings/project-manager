# ADR-0001: Use Repository Documentation as the Primary Status Source

## Status

Accepted

## Context

Project Manager needs to summarize the state of multiple GitHub repositories. Raw GitHub activity is useful, but it does not reliably answer questions like:

- What is the project trying to accomplish right now?
- What milestone matters next?
- Is a quiet repo intentionally paused or actually stale?

The tracked repositories are expected to share a common documentation structure, which makes project docs a stronger source of intent than issues, pull requests, or commit counts alone.

## Decision

For v1, Project Manager will treat repository documentation as the primary source of truth for status intent.

The app should read a small set of agreed files from each tracked repo:

- `README.md`
- `docs/project_charter.md`
- `docs/implementation_schedule.md`
- recent `session_logs/`

GitHub issues, pull requests, and commits will be used as supporting evidence and freshness signals, not the canonical status source.

## Consequences

### Positive

- Repo summaries can reflect intent instead of only motion.
- The product benefits directly from the team's existing documentation habits.
- A curated, documentation-aware dashboard can be useful before a larger analytics platform exists.

### Negative

- The system depends on documentation consistency across tracked repos.
- Missing or weak docs reduce summary quality.
- The parser must handle partial or inconsistent structure gracefully.

## Alternatives Considered

### GitHub Activity Only

Rejected because activity alone cannot reliably capture current goal, milestone, or intentional pauses.

### Require a Generated Summary File in Every Repo

Deferred. This may become attractive later, but it adds workflow overhead too early and is unnecessary while the repos already share a predictable documentation shape.
