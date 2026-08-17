# SelfContext Vision

## The Problem

People repeatedly explain the same history, preferences, goals, constraints, and examples to different AI systems and to different sessions of the same system. The resulting context is fragmented across chat histories, provider-specific memories, documents, and personal notes. It is difficult to inspect, correct, move, or preserve.

## The Thesis

Persistent personal context should belong to the person rather than to a model, AI provider, harness, application, or chat session.

SelfContext makes that context a portable Context Vault: ordinary interconnected Markdown files with lightweight metadata, provenance, lifecycle information, and links. The selected model and harness provide intelligence and execution, while the vault remains the user's durable knowledge asset.

## The Core Product Bet

SelfContext is not only a portable memory store. Its deeper purpose is to help maintain a trustworthy, evolving, user-correctable working model of the person.

Agents may organize the context, identify patterns, preserve provenance, and surface gaps or contradictions. The user remains the owner and final authority. Trust is selective and claim-level: it depends on evidence, verification, freshness, and clearly stated uncertainty rather than repeated model-generated text.

This is not an attempt to create a complete or objective personality profile. It is an evidence-grounded representation of the person's context, history, goals, patterns, preferences, and unresolved questions.

## Continuity of Thought

SelfContext exists to support continuity of useful reasoning. Durable context
should help a person and their existing AI harness continue a line of thought
without starting from zero, while the conversation itself remains temporary
unless something earns a place in the vault.

The conceptual lifecycle is:

```text
durable context
      ↓
targeted retrieval
      ↓
contextual reasoning
      ↓
ephemeral conversation
      ↓
optional checkpoint
      ↓
smallest durable update
      ↓
existing Context Vault
```

The current foundation provides local skills for targeted retrieval, contextual
reasoning, ingest, query, checkpoint, review, validation, maintenance, and
optional context receipts. The lifecycle is not automatic: conversation and
reasoning are ephemeral by default, checkpoint routes candidates through the
existing persistence rules, and durable updates remain deliberate and
user-correctable. Brainstorming and decision-making are horizontal workflows,
not additional verticals or storage systems.

The principles are:

1. **Memory accumulation is not the goal.** A larger vault is not, by itself, a better one.
2. **The purpose of context is to improve future reasoning.** Durable context earns its place by making later thinking more useful.
3. **A conversation is ephemeral by default.** Conversation history is not the canonical vault.
4. **Reasoning is not automatically memory.** Exploration and analysis do not become durable merely because they occurred.
5. **Generated assistant suggestions are not facts about the user.** They remain suggestions or derived material unless the user deliberately confirms something as context.
6. **Only information that earns future reuse value should become durable context.** Relevance and expected continuity matter more than completeness.
7. **The user remains the final authority over durable context.** The user can inspect, correct, retain, or remove it.
8. **Context should be inspectable, correctable, and portable.** Plain files and visible provenance keep those properties concrete.
9. **The system should become better at deciding what NOT to store, not merely better at storing more.** Selectivity is a product capability, not a failure to remember.

These principles extend the existing commitments to provenance, visible
contradictions, explicit uncertainty, freshness, user ownership, and
local-first storage. They do not replace the evidence and lifecycle rules that
keep durable context trustworthy.

## Design Commitments

- **User ownership:** The source of truth is a local directory the user can copy, inspect, edit, back up, or delete.
- **Model and harness independence:** Switching models or harnesses should not require rebuilding personal context.
- **Human readability:** A person or a sufficiently capable generic model should be able to understand the vault as plain files.
- **Portability:** The vault should remain useful if SelfContext's operational implementation disappears.
- **Evidence and provenance:** User statements, source-derived facts, agent observations, and derived syntheses remain visibly distinct.
- **Lifecycle:** Context can be current, stale, unverified, contradicted, or in need of review. It is more than a static memory dump.
- **Natural interaction:** Users express intent in ordinary language. Skills determine whether a request means ingest, query, review, lint, or advice.
- **Smallest useful system:** Markdown and skills should earn their place before code or infrastructure is added.
- **Explicit maintenance:** ordinary lint is fast and deterministic; deep lint is deterministic; deep review is read-only by default; deep update is explicitly authorized and backed up.
- **Selective contracts:** available verticals are not automatically enabled, and applied contract versions remain visible in schema 0.2.

## Why Markdown and Links

Markdown is easy to read, edit, diff, copy, archive, and open in many tools. YAML frontmatter provides enough structured metadata for lifecycle and validation without making a database canonical. Standard Markdown links provide useful connections in Obsidian and generic file-based agents while keeping the format interoperable.

The vault is therefore a small personal-context structure, not a generic wiki or arbitrary document dump. A meaningful concept can stand alone, connect to related concepts, and point back to evidence. A trivial answer does not need to become a new permanent page. Compiled catalogs and disposable lexical search may improve navigation without changing the Markdown source of truth.

## Lifecycle, Not Just Retrieval

Useful context changes over time. Employment history may be stable, while a current goal or project description may become stale quickly. SelfContext should help ingest new information, connect it to what already exists, surface unresolved observations and contradictions, review freshness, and validate the structure.

The lifecycle is deliberately conservative. An agent may notice a recurring pattern, but it must not silently promote that inference to personal fact. User confirmation remains the boundary between an observation and stable context.

## Long-Term Direction

Career was the first vertical because it provided a concrete, evidence-rich use
case. Writing is a separate vertical for evidence-backed communication and
writing context, and Learning records what the person understands and how that
understanding evolves. Relationships preserves intentional shared context with
other people, while Media / Taste preserves reactions to cultural works and the
evidence behind evolving preferences. Ventures / Projects preserves the
lifecycle of meaningful initiatives, opportunities, experiments, and
collaborations without becoming a task manager or CRM. The core should remain
useful across domains without defining domain schemas itself. Every vertical and Advisor Pack
should consume the same portable context rather than create competing memory
systems.

Guided Discovery may eventually identify important gaps and ask targeted
questions. It is a future workflow, not part of the current foundation.

## Success Test

If the model, harness, operational skills, Obsidian, or search implementation disappeared tomorrow, the copied `vault/` directory should still contain understandable, useful knowledge about its owner.
