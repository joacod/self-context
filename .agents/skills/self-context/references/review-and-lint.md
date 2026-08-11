# Review and Lint Workflow

Review asks a human to resolve epistemic or lifecycle issues. Lint provides
deterministic structural checks. They complement each other; a clean lint run
does not prove that a claim is true.

If review will resolve a page or append a review/lint operation to `log.md`,
create the pre-write backup described in [Vault Backups](backups.md) before the
first write. A read-only review or lint run needs no backup.

## Review

Orient from the schema, root index, and recent log. Then inspect:

- durable pages with `status: review`, pages under `review/observations/`, and
  any `agent_inference` pages;
- claims whose `stale_after` date has passed;
- relevant current goals, role descriptions, or projects with missing freshness
  metadata;
- contradictions, ambiguous dates, and competing versions of a claim;
- important pages without a source or user verification;
- new changes that were not linked from affected indexes.

For Writing, also inspect whether an observation is scoped to an evidenced mode
or period, whether generated material has been kept out of primary evidence,
whether human revision signals are supported by meaningful deltas, and whether
beliefs or career facts have been copied into the Writing vertical. The linter
cannot decide these semantic questions; keep them visible for human review.

For Learning, inspect whether a page describes the person’s knowledge rather
than merely a resource, whether its qualitative state is scoped and supported,
whether exposure has been kept separate from understanding, and whether gaps,
misconceptions, corrections, and prerequisites retain dated evidence. Check
that Career projects and Writing artifacts are linked rather than duplicated,
and that generated explanations remain derived. The linter cannot decide
whether a person understands a concept; keep that judgment evidence-backed and
reviewable.

For a broad semantic review, sample recent meaningful ingests from `log.md` and
check category coverage: explicit context useful across domains should not be
stranded in a vertical, and vertical facts should not be duplicated into
`core/` merely because they are important. Check that reusable analyses are in
`derived/` and remain visibly derived. Do not copy conclusions from a derived
page into factual context without underlying evidence and the appropriate
assertion kind.

Treat `verified: null` as an ordinary unconfirmed state, not as a finding by
itself. Surface it when the claim is important, current-sensitive, ambiguous,
contradictory, explicitly requested for review, or otherwise likely to affect a
future answer. Do not turn a broad vault review into a prompt for every page.

For selected current-state items without an explicit deadline, report unknown
freshness only when the page is relevant to the review or query. The default
ingest policy assigns a 90-day deadline to narrow, important current-state
anchors; it leaves other pages at `stale_after: null`.

For every finding, show the page, the evidence or metadata that caused the
finding, and a suggested human action. Do not resolve an inference, conflict,
or goal silently. A user can confirm an observation, reject it, revise it, or
leave it unresolved. Record meaningful resolutions in `log.md`.

## Deterministic Lint

Run the bundled validator from the repository root:

```bash
python3 .agents/skills/self-context/scripts/lint_vault.py vault
```

Use a copied or explicitly selected vault path when validating another vault.
The script checks:

- required control files;
- frontmatter delimiters and required metadata on durable pages;
- required `description` and `tags` fields on durable pages;
- allowed type, status, and assertion values;
- malformed or broken local Markdown links;
- source references that do not resolve;
- path-aware exemptions for root controls and index pages;
- explicit exclusion of `.obsidian/` viewer state; project-root `backups/`
  archives are outside the vault path and are not scanned;
- duplicate IDs when present and duplicate titles as warnings;
- invalid or expired `stale_after` dates; and
- unverified observations or inference pages.

The linter does not decide whether a claim is true, important, or in need of
confirmation. It should not warn merely because a normal page has
`verified: null` or `stale_after: null`.

The script is intentionally dependency-free and does not replace semantic
review. It reports errors and warnings, returns a non-zero status for errors,
and leaves the vault unchanged. Inspect the output rather than claiming that a
clean result proves correctness.

After linting, manually inspect index navigation, provenance quality,
contradictions, and whether derived pages remain visibly derived. Log a
meaningful lint or review operation and report findings to the user.
