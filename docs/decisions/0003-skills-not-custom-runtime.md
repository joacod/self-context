# ADR 0003: Use Skills with the Existing Harness

- **Status:** Accepted
- **Date:** 2026-08-07

## Context

SelfContext needs operational behavior for ingesting, querying, reviewing, and validating a vault. The user's selected model and existing harness already provide the agent loop and execution environment.

## Decision

Ship the operational behavior as canonical project-local Agent Skills under `.agents/skills/`. The SelfContext skill handles the core lifecycle, and Advisor Packs such as Career Advisor specialize reasoning. The existing harness and selected model remain the runtime.

## Consequences

- The project stays small and can work across compatible harnesses.
- Skill instructions can evolve independently from the portable vault.
- The skills must have clear trigger descriptions and progressive disclosure rather than becoming one large instruction file.
- Compatibility adapters, if ever added, should load or point to the canonical skills rather than duplicate them.

## Alternatives Rejected

A custom agent runtime, dedicated SelfContext subagents, a custom chat interface, and harness-specific duplicate skill implementations were rejected because they would make the operational layer harder to replace and maintain.
