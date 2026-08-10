# SelfContext Roadmap

This roadmap describes intended experiments, not promises. Each phase is completed only after its behavior is validated and the build plan is updated.

The v0.1 bootstrap is complete. The next practical experiment is to dogfood the
skills with real career information while keeping the private vault local and
separate from tracked project files.

## v0.1

- Portable vault format.
- First-run bootstrap.
- Ingest.
- Query.
- Review.
- Lint.
- Career vertical.
- Career Advisor Pack.
- Obsidian compatibility.
- Multi-session continuity.
- Local pre-write ZIP backups with retention of the latest three archives.

The v0.1 implementation should remain mostly Markdown, Agent Skills, references, and only the smallest deterministic validation code that earns its place. It should not introduce a custom runtime, server, database, embeddings, MCP, background service, or telemetry.

## v0.2

- Guided Discovery.
- Context coverage and gap analysis.
- Targeted questions.
- Stronger stale-context review.

Guided Discovery is intentionally not part of v0.1 review. Review should surface issues; it should not become a long interview system yet.

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
