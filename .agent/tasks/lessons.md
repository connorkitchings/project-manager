# Lessons Learned

> Patterns and mistakes to avoid. Review at session start. Update after any correction.

---

## How to Use This File

1. **Review at session start** — Check for relevant lessons before starting work
2. **Add after corrections** — Whenever the user corrects you, capture the pattern
3. **Iterate ruthlessly** — Refine rules until the same mistake stops happening

---

## Correction Patterns

> Lessons from user corrections. Each entry captures the mistake, the rule to prevent it, and the date.

### [Date: 2026-04-25]

**Mistake:**
> `super()` in `RepoDetail.to_dict()` failed on Python 3.11 CI with `TypeError: super(type, obj): obj must be an instance or subtype of type`. Worked locally on Python 3.14.

**Root Cause:**
> `@dataclass(slots=True)` doesn't create the `__class__` implicit closure cell on Python 3.11, so `super()` has no reference to the class.

**Rule Added:**
> Never use bare `super()` in `@dataclass(slots=True)` subclasses. Use explicit `ParentClass.method(self)` instead.

**Example:**
> Replace `super().to_dict()` with `RepoSummary.to_dict(self)`.

---

### [Date: 2026-04-25]

**Mistake:**
> Pushed code without checking that CI workflows would pass. Three rounds of CI fixes were needed.

**Root Cause:**
> Didn't check CI workflow files before pushing. The workflows had pre-existing issues (missing tsconfig paths, wrong `--extra` flags, missing permissions) that only surfaced in CI.

**Rule Added:**
> Before pushing, review CI workflow files and run equivalent checks locally: `tsc --noEmit` from `ui/`, `uv sync --extra docs`, `uv sync --extra security`.

**Example:**
> Run `npx tsc --noEmit` from `ui/` directory before pushing frontend changes. Check that all `--extra` and `--group` flags in CI match `pyproject.toml` structure.

---

### Template for New Entries

```markdown
### [Date: YYYY-MM-DD]

**Mistake:**
> [Brief description of what went wrong]

**Root Cause:**
> [Why it happened - be honest]

**Rule Added:**
> [Specific actionable rule]

**Example:**
> [What you should have done]
```

---

## Categories

### Code Quality
- [ ] Lazy fixes / temporary workarounds
- [ ] Missing tests
- [ ] Over-engineering
- [ ] Not considering edge cases

### Process
- [ ] Not planning before implementing
- [ ] Skipping verification
- [ ] Not asking clarifying questions
- [ ] Implementing without approval

### Context
- [ ] Not reading relevant docs first
- [ ] Missing important files
- [ ] Not checking recent session logs
- [ ] Ignoring existing patterns in codebase

### Communication
- [ ] Not explaining changes
- [ ] Making assumptions without checking
- [ ] Not providing options
- [ ] Missing handoff notes

---

## Review Checklist

Before each session, check:

- [ ] Read last 10 entries for relevant patterns
- [ ] Any new lessons since last session?
- [ ] Rules still make sense / haven't become outdated?

---

## Success Metrics

Track improvement over time:

- [ ] Fewer repeated mistakes
- [ ] Corrections decrease over time
- [ ] Rules are specific and actionable

---

## Links

- Principles: `.agent/PRINCIPLES.md`
- Start session: `.agent/skills/start-session/SKILL.md`
- End session: `.agent/skills/end-session/SKILL.md`

---

**Update this file after EVERY correction. The goal is to make the same mistake once.**
