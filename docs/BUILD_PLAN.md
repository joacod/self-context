# SelfContext Bootstrap Build Plan

## Purpose

This document is the handoff point for a new AI session. It records the phased bootstrap status, acceptance criteria, and decisions that must remain stable while SelfContext is built.

The project is intentionally implemented one phase at a time. After each phase, validate only that phase, update this document, show `git status --short`, suggest a commit message, and stop for user review. Do not start the next phase without explicit user direction.

## Current State

- **Current phase:** Phase 2 - Core SelfContext skill complete; no later phase is active.
- **Repository state:** Tracked foundation documentation and the canonical project-local SelfContext skill are present alongside the original `LICENSE` and funding configuration.
- **Private vault state:** No `vault/` directory is present. This is expected; the repository must not depend on an ignored empty directory.
- **Next authorized phase:** Phase 3 - Career Advisor skill, only after the user explicitly says to continue.

## Non-Negotiable Constraints

- Ordinary Markdown, YAML frontmatter, standard Markdown links, and simple directories remain the portable contract.
- `vault/` is private, entirely Git-ignored, and must never be force-added.
- The vault is the source of truth and must not depend on a harness, provider, model, Obsidian, or operational implementation.
- SelfContext uses existing harnesses and Agent Skills; it does not ship a custom agent runtime or dedicated runtime subagents.
- No canonical database, graph database, vector database, embeddings, MCP server, background service, server, custom chat interface, telemetry, or automatic sync in v0.1.
- User-stated facts, source-derived facts, agent inferences, and derived syntheses must remain distinguishable.
- Natural language is the canonical interface. Commands may be optional conveniences only.
- Never place real personal information in tracked examples, tests, evaluations, or documentation.

## Phases

### Phase 1 - Repository Foundation

**Status:** Complete.

Create the tracked project foundation without creating skills, runtime code, or personal vault content.

Expected files:

- `.gitignore`
- `README.md`
- `AGENTS.md`
- `docs/VISION.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/BUILD_PLAN.md`
- Focused ADRs under `docs/decisions/`

Acceptance criteria:

- The project purpose, boundaries, quick start, privacy model, and v0.1 scope are understandable from the README.
- Repository guidance routes vault work through SelfContext and career reasoning through SelfContext plus Career Advisor.
- Architecture explains the tracked/private boundary, dependency direction, lifecycle, provenance, query persistence, and rejected infrastructure.
- The roadmap documents v0.1, v0.2, and later possibilities without promising them.
- The root `/vault/` path is ignored, and no vault content is tracked.
- No SelfContext skill, Career Advisor skill, runtime code, or real personal data is created.

Validation recorded for this phase:

- `git diff --check` passed.
- `git check-ignore -v --no-index vault/.gitkeep vault/SCHEMA.md vault/example.md` confirmed the root `/vault/` rule.
- `git ls-files 'vault' 'vault/**'` returned no tracked vault content.
- The Markdown link review found only standard links, and no `[[wikilinks]]` were introduced.
- `git status --short --ignored` showed only the intended foundation changes; no vault directory exists to report.

### Phase 2 - Core SelfContext Skill

**Status:** Complete.

Use the installed `skill-creator` workflow to create `.agents/skills/self-context/`. Define the v0.1 vault schema and implement instructions for initialization, existing-vault orientation, ingest, query, review, lint, lifecycle, provenance, links, indexes, logs, epistemic separation, and substantial-query persistence. Add a minimal deterministic validator only if the skill-creator evaluation shows that it materially improves reliability.

Acceptance criteria:

- A missing vault initializes automatically on the first operation requiring one.
- An existing copied vault is recognized and oriented from `SCHEMA.md`, `index.md`, and recent `log.md` entries.
- Ingest updates related concepts rather than creating avoidable duplicates.
- Queries remain targeted and trivial retrievals do not pollute the vault.
- Review and lint surface important structural, provenance, freshness, inference, and contradiction issues.
- The skill remains portable and career-aware without making career the core schema.

Implementation and validation recorded for this phase:

- `.agents/skills/self-context/SKILL.md` is the concise control plane; detailed schema, initialization, ingest, query, and review/lint procedures are progressively disclosed through five direct references.
- The v0.1 vault contract defines `SCHEMA.md`, `index.md`, `log.md`, core/career/review/source/derived areas, standard relative Markdown links, YAML frontmatter, provenance, freshness, and epistemic categories.
- `scripts/lint_vault.py` is dependency-free and checks required control files, frontmatter, metadata values, local links, source containment, schema version declarations, stale dates, duplicate IDs/titles, and unverified observations.
- The installed `skill-creator` `quick_validate.py` passed after loading its missing `PyYAML` dependency into an isolated temporary directory; no project dependency was added.
- The linter passed an ephemeral clean synthetic vault and correctly reported a broken link, stale claim, and unverified observation in an invalid synthetic vault.
- `lint_vault.py` syntax, both JSON eval files, and `SKILL.md` frontmatter all validated successfully.
- A trigger-evaluation set is tracked under `evals/trigger-evals.json`. The installed trigger runner could not produce a meaningful score because the local Claude CLI is unauthenticated; `claude -p` returned `Not logged in`. Full trigger and operational evaluation remains Phase 4 work.
- `git diff --check` passed, no `vault/` directory exists, and no vault content is tracked.
- Phase 2 follow-up: `.gitignore` now excludes Python caches and test artifacts, temporary Claude/eval workspaces, generated skill/build packages, and common OS/editor files. Synthetic evals use `John Doe`/`John` and `MyContext Systems` as fictional placeholders.

### Phase 3 - Career Advisor Skill

**Status:** Pending.

Use the installed `skill-creator` workflow to create `.agents/skills/career-advisor/`. It must consume evidence retrieved through SelfContext, distinguish evidence from uncertainty and recommendations, and avoid inventing experience or silently changing user goals.

### Phase 4 - Operational Evaluation

**Status:** Pending.

Use synthetic scenarios and the skill-creator evaluation workflow where practical. Exercise first-run initialization, updates, links, trivial and substantial queries, unverified observations, corrections, stale context, lint failures, grounded and under-evidenced career advice, fresh-session orientation, copied vaults, and natural-language trigger boundaries.

### Phase 5 - First-Run Dry Run and v0.1 Completion

**Status:** Pending.

Run the complete synthetic workflow from a nonexistent vault through initialization, ingest, cross-linking, query, review, lint, career advice, and conceptual fresh-session continuity. Inspect the result as plain Markdown and in the Obsidian compatibility model. Remove the synthetic private vault, polish documentation, record limitations, and identify dogfooding with real career information as the next experiment.

## Key Decisions

- [Markdown and standard links are canonical](decisions/0001-markdown-canonical.md).
- [The vault is local, private, and Git-ignored](decisions/0002-git-ignored-vault.md).
- [Skills use the existing model and harness](decisions/0003-skills-not-custom-runtime.md).
- [Epistemic categories remain separate](decisions/0004-epistemic-separation.md).
- [v0.1 deliberately rejects infrastructure](decisions/0005-no-v01-infrastructure.md).
- [Core context stays extensible while career is the first vertical](decisions/0006-core-and-career-vertical.md).

## Phase Handoff Rules

Only the phase explicitly marked in progress may be implemented. A later session should first read this document, inspect the worktree, and verify the user's explicit instruction before proceeding. User review, optional fixes, and user-managed commits happen between phases.
