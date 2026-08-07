# ADR 0006: Extensible Core with Career as the First Vertical

- **Status:** Accepted
- **Date:** 2026-08-07

## Context

Personal context may eventually span multiple domains, but designing several hypothetical domains now would add complexity and dilute the first useful use case. Some information is broadly personal, while other information is meaningful only within a domain.

## Decision

Separate core personal context from vertical-specific context. Career is the only implemented v0.1 vertical and the Career Advisor is its first Advisor Pack. The core defines shared lifecycle, provenance, link, review, and validation behavior without hardcoding the entire system around career. Future verticals and packs must consume the same vault rather than create competing memory formats.

## Consequences

- v0.1 can be concrete and testable while preserving a clear extension point.
- Career concepts may cover roles, history, projects, skills, achievements, leadership, mentoring, public work, and professional goals.
- The architecture does not prescribe schemas for health, finance, relationships, or other future domains.
- Career advice must retrieve evidence through SelfContext and must not own or duplicate career facts.

## Alternatives Rejected

A career-only foundation and a speculative collection of multiple vertical schemas were both rejected: the former limits portability across personal contexts, while the latter creates premature abstractions.
