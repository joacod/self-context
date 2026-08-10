# SelfContext Roadmap

This roadmap describes intended experiments, not promises. A change is ready
when its behavior is validated and documented; Git records the change history.

## Current Foundation

The current system provides:

- a portable Markdown vault with YAML frontmatter and standard links;
- first-run initialization and orientation of existing vaults;
- natural-language ingest, query, review, and lint workflows;
- shared provenance, lifecycle, freshness, and epistemic boundaries;
- local pre-write ZIP backups with retention of the latest three archives;
- Obsidian compatibility and multi-session continuity; and
- separate Career and Writing verticals with replaceable Advisor Packs.

## Current Vertical Work

Each vertical has its own scope and experiment surface while reusing the shared
SelfContext lifecycle:

| Vertical | Current behavior | Next useful experiment |
| --- | --- | --- |
| Career | Evidence-backed roles, projects, skills, goals, and professional reasoning | Dogfood the workflows with real career information while keeping the vault local |
| Writing | Evidence-aware source comparison, selective profile updates, and writing reasoning | Use different authored modes and check whether the profile becomes more accurate without merely becoming larger |

Neither vertical adds a competing memory format, custom runtime, universal
taxonomy, or automatic promotion of generated output into facts.

## Near-Term Experiments

- Guided Discovery for context coverage and gap analysis.
- Targeted questions that remain bounded rather than becoming an open-ended
  interview.
- Stronger stale-context review when freshness matters to an answer.

## Later Possibilities

- Additional personal-context verticals.
- More Advisor Packs.
- Optional harness adapters that load the canonical project skills.
- Optional disposable local search indexes if vault scale requires them.
- User-controlled off-device backup copies and sync.
- Selective disclosure.
- Stronger privacy and encryption workflows.
- Automated refresh of explicitly approved sources.

These possibilities must preserve the portable Markdown vault and must not silently turn generated interpretation into user-confirmed fact.
