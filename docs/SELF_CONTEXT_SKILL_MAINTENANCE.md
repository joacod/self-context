# SelfContext Skill Maintenance

This guide is for changing the tracked SelfContext skill, not for ordinary
Context Vault operations. Keep the skill portable, progressive, and useful when
its current harness or model is unavailable.

## Layering

Use the smallest canonical layer that owns the behavior:

- **Frontmatter description:** describe when the skill should trigger and its
  important non-goals. The loader always reads this metadata before any
  references.
- **`SKILL.md`:** keep the control plane here: operating boundaries, operation
  selection, safety rules, context orientation, and pointers to procedures.
- **`references/*.md`:** put detailed procedures, schemas, lifecycle steps, and
  vertical-specific workflows here. Add a reference when a cohesive procedure
  needs progressive disclosure; do not duplicate shared rules across files.
- **`scripts/`:** keep deterministic parsing, validation, backup, indexing, and
  search helpers here rather than asking the model to reproduce them.
- **`evals/`:** preserve synthetic behavior and trigger coverage. Never use real
  vault content in tracked evals or documentation. Use `John Doe` (or `John`)
  for the synthetic user and `MyContext Systems` when a company name is needed;
  keep other named people only when a scenario genuinely needs them.

`SKILL.md` should remain comfortably below 500 lines. Reference files may be
larger, but files over roughly 300 lines should have a table of contents.

## Description budget

Agent Skill descriptions have a hard maximum of 1024 characters. Treat 900 as
the recommended working budget so future additions do not break loading.
Descriptions should contain trigger vocabulary and boundaries, not detailed
implementation instructions that already belong in `SKILL.md` or a reference.

The repository guard checks every tracked `.agents/skills/*/SKILL.md`:

```bash
python3 scripts/validate_skill_metadata.py
```

The same check runs through the canonical repository validation command:

```bash
python3 scripts/validate_repo.py
```

When changing a description, preserve both positive trigger cases and nearby
non-trigger cases. Use `evals/trigger-evals.json` as the regression corpus, and
run the broader skill evaluation corpus when the behavior or routing meaning
changes rather than merely shortening wording.

## Adding a capability

1. **State the observable behavior.** Identify what a user can ask for, the
   expected result, relevant evidence, and explicit non-goals.
2. **Classify ownership.** Put shared vault lifecycle and schema rules in the
   SelfContext core. Put vertical evidence and procedures in that vertical's
   documented area. Keep Advisor Pack reasoning separate from storage and
   provenance.
3. **Choose the canonical file.** Extend an existing procedure when the
   behavior belongs there; create a new reference only for a cohesive area that
   can be loaded independently.
4. **Add the routing pointer.** If the skill needs the new procedure, update the
   operation-selection or reference map in `SKILL.md` so it says when to read
   it. Do not rely on a filename alone.
5. **Add synthetic coverage.** Add behavior evals for the new operation and
   trigger evals when the invocation boundary changes. Keep examples fictional
   and provenance-aware.
6. **Validate the whole contract.** Run metadata validation, targeted tests,
   `python3 scripts/validate_repo.py`, and the relevant direct test or CI
   commands. Inspect the final diff for duplicated rules, private data, and
   accidental changes.

## Description-change checklist

Before committing a description change, confirm:

- it says what the skill does and when to use it;
- important positive trigger phrases remain represented;
- important near-miss or generic-use exclusions remain represented;
- detailed lifecycle instructions remain in the body or references;
- the parsed description is below 900 characters when practical;
- trigger evals still cover the changed boundary; and
- the repository metadata guard passes.

Do not automatically truncate a description. Shorten it deliberately so the
trigger contract and safety boundaries remain understandable.
