# Knowledge Base

This document captures reusable patterns and operating lessons discovered while building Project Manager.

Use the format `[KB:PatternName]` to reference entries from other docs or session logs.

---

## `[KB:RepoStatusSourcePriority]`

- **Context:** Project Manager needs a trustworthy repo summary, but GitHub activity alone does not explain intent.
- **Pattern:** Prefer project docs for the current goal and milestone. Use GitHub commits, pull requests, and issues as evidence of freshness and motion.
- **Usage:** Apply this whenever documentation and activity disagree or when deciding which source should populate a summary field.
- **Discovered In:** `docs/project_charter.md` kickoff decisions on 2026-04-21

## `[KB:GracefulMissingDocs]`

- **Context:** Not every tracked repo will expose every expected file.
- **Pattern:** Report missing sources as structured gaps and continue building the rest of the status snapshot.
- **Usage:** Parser and UI logic should surface partial confidence instead of failing hard.
- **Discovered In:** Initial architecture definition, 2026-04-21

## `[KB:RealRepoMarkdownDrift]`

- **Context:** Live repos do not all use the same markdown conventions for session logs, README metadata blocks, or implementation schedules.
- **Pattern:** Prefer markdown-shape heuristics over template-only exact matches. Support both bullet-style and paragraph-style `**Goal:**` fields, skip README metadata paragraphs when extracting summaries, and ignore schedule legends when searching for blockers.
- **Usage:** Apply this when validation against a real repo shows a missing goal, a noisy summary, or a false blocker.
- **Discovered In:** Multi-repo validation against `FRED`, `panicstats`, `JamBandNerd`, and `Vibe-Coding` on 2026-04-21
