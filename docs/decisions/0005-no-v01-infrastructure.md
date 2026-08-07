# ADR 0005: Do Not Add Infrastructure in v0.1

- **Status:** Accepted
- **Date:** 2026-08-07

## Context

The first useful version can be made from Markdown, skills, references, and perhaps a tiny validator. Additional infrastructure would add operational and privacy costs before the core lifecycle is proven.

## Decision

v0.1 has no canonical database, graph database, vector database, embeddings, RAG framework, MCP server, API server, background service, sync service, authentication system, analytics, telemetry, or custom UI. Deterministic scripts are allowed only when they materially improve a fragile operation such as linting, and any generated indexes or caches remain disposable.

## Consequences

- The implementation remains local, inspectable, and easy to copy.
- The model performs targeted retrieval from files rather than semantic or vector search.
- Scale-related optimizations must wait for evidence that the portable file workflow needs them.
- Future infrastructure must preserve the vault as the canonical source and require a documented architectural decision.

## Alternatives Rejected

Adding a database, embeddings, server, or custom interface at bootstrap was rejected because it would solve hypothetical scale or product problems before the basic format and lifecycle have been validated.
