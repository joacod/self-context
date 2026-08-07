# ADR 0004: Preserve Epistemic Categories

- **Status:** Accepted
- **Date:** 2026-08-07

## Context

The subject of the vault is a person. An agent can produce plausible interpretations that become falsely reinforced if they are stored and later treated as facts. Source material and user recollections also have different evidentiary status.

## Decision

SelfContext distinguishes user-stated or user-confirmed facts, source-derived facts, agent inferences, and derived syntheses. Unverified observations remain visibly reviewable until the user confirms or rejects them. Derived queries and advice cannot silently modify factual context or user goals.

## Consequences

- Advice can state what is evidenced, what appears likely, what is unknown, and what is recommended.
- Review and lint must be able to surface unresolved observations, missing provenance, stale claims, and contradictions.
- Ingest workflows require judgment about provenance without forcing unnecessary ceremony on every small conversational detail.
- The vault avoids an automatically generated static personality profile.

## Alternatives Rejected

Flattening all statements into undifferentiated facts, or allowing model confidence to substitute for human verification, was rejected because it creates an artificial evidence loop.
