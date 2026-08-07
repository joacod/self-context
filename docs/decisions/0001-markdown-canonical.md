# ADR 0001: Markdown and Standard Links Are Canonical

- **Status:** Accepted
- **Date:** 2026-08-07

## Context

SelfContext must remain useful when the current model, harness, viewer, or operational skill changes. A provider-specific memory store or an application-specific graph would make the durable context difficult to inspect and move.

## Decision

The Context Vault uses ordinary Markdown files, YAML frontmatter, simple directories, and standard relative Markdown links as its canonical format. Obsidian is an optional viewer and editor, not a dependency. Obsidian wikilinks are not canonical.

## Consequences

- A person or generic file-based agent can inspect the vault without SelfContext tooling.
- Files are easy to copy, diff, back up, and open in multiple applications.
- Links must be maintained as portable relative Markdown links rather than relying on application-specific syntax.
- Rich search or graph views may be added later only as disposable tooling.

## Alternatives Rejected

Canonical databases, graph databases, embeddings, vector stores, and Obsidian-only syntax were rejected because they make replaceability and portability worse without being necessary for v0.1.
