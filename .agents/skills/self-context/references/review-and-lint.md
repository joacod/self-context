# Review and Lint Workflow

Review asks a human to resolve epistemic or lifecycle issues. Lint provides
deterministic structural checks. They complement each other; a clean lint run
does not prove that a claim is true. Ordinary review remains targeted; an
explicit “deep review” selects the full, read-only maintenance protocol in
[Deep Maintenance](deep-maintenance.md). A normal request such as “review my
current role” must not trigger a full-vault scan.

If review will resolve a page or append a review/lint operation to `log.md`,
complete the authorized writes and relevant validation, then create the
post-write backup described in [Vault Backups](backups.md). A read-only review
or lint run needs no backup.

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

For Relationships, inspect whether each page is about the user's relationship
rather than an unrelated third-party dossier, whether reported statements and
sources are labeled, whether commitments are real rather than vague tasks, and
whether behavioral observations avoid unsupported judgments or sensitive
inferences. Check deletion, redaction, stale threads, contradictions, and links
to Career or other owning verticals.

For Media / Taste, inspect whether work pages preserve the user's actual
reaction rather than consumption or external metadata, whether inferred
patterns have sufficient independent evidence, and whether exceptions, dates,
contradictions, and generated-artifact boundaries remain visible. Check that
recommendations stay derived and that taste pages do not infer sensitive
identity, ideology, health, or personality.

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
python3 .agents/skills/self-context/scripts/lint_vault.py --deep --format text vault
python3 .agents/skills/self-context/scripts/lint_vault.py --deep --format json vault
```

Ordinary lint is the fast backward-compatible path and never migrates. Deep
lint is deterministic and read-only; schema migration is a separate operation
owned by the [Migration procedure](migration.md). JSON output contains schema version, available contracts,
enabled verticals, applied contracts, a snapshot ID, compact page metadata,
link/index relationships, findings, and severity counts, never complete page
bodies. Neither path produces a numeric vault-health score.

The deep-lint `pages` inventory is intentionally compact. Valid entries expose
`path`, stable `id`, `title`, `description`, `aliases`, `tags`, `type`,
`assertion_kind`, `status`, lifecycle dates, `owner_index`, catalog `vertical`,
`content_hash`, normalized `outbound_links` and `inbound_links`, the raw valid
frontmatter `sources` list, and `source_relationships`. A source relationship
records `original`, `normalized_target`, `internal`, `external`, `exists`, and
`target_kind`; it is a provenance pointer, not an authority or truth score.
Body/context links remain ordinary navigation metadata and do not become
provenance merely because they point at a source-looking page. Deep-lint JSON
contains no complete page bodies, source transcripts, snippets, generated task
packets, or ignored operational state. Tags and aliases can guide page
selection without becoming personal claims.

A newer generated or updated timestamp on a linked source produces only the
review signal: “Linked source has a newer generated or updated timestamp than
this derived synthesis. Review whether regeneration is needed.” It does not
prove that the change was material, that the source was decisive, that the
synthesis is wrong, or that regeneration is mandatory.

Deep lint has two distinct rule layers. Universal filesystem and decoding safety
checks apply everywhere in canonical content below the vault root, including
custom top-level areas: symlinks, unreadable files, invalid UTF-8, and unsafe
internal link targets are reported wherever they occur. Explicitly noncanonical
viewer/backup state remains excluded from canonical inventory and snapshot
semantics. SelfContext semantic, schema, vertical-contract, managed-catalog,
reachability, and ownership rules apply only to managed areas. Custom areas are
preserved and are not added to retrieval, managed indexes, vertical contracts,
or migrations by lint.

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

Deep lint additionally checks canonical-content symlinks, UTF-8 failures,
root reachability, nearest-index ownership, managed catalog synchronization,
strict managed-marker structure, missing or ambiguous catalog blocks, catalog
owner mismatches, metadata that prevents safe rendering, dead entries,
title/alias collisions, duplicate IDs/content, type/assertion/path
compatibility, lifecycle and supersession links, source cycles, derived source
chains, schema-specific vertical contract validity and currency, custom top-level
areas, recent log links, and exclusion of `.obsidian/` and project-root backups.
Older applied contracts produce an update-available warning; matching versions
produce no currency finding; future versions, unknown IDs, invalid versions,
and duplicate IDs are errors. A weakly connected page is a warning, not an
automatic error.

The script is intentionally dependency-free and does not replace semantic
review. It reports errors and warnings, returns a non-zero status for errors,
and leaves the vault unchanged. Inspect the output rather than claiming that a
clean result proves correctness.

After linting, manually inspect index navigation, provenance quality,
contradictions, and whether derived pages remain visibly derived. Log a
meaningful lint or review operation and report findings to the user.
