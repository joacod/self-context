# Developer Diagnostic Overlay

This is an explicit, temporary dogfooding overlay for one ordinary
SelfContext request. It is not a third operating mode, a transcript facility,
telemetry system, daemon, service, or harness integration.

## Activation and lifecycle

Activate only when the raw prompt begins with the exact ASCII prefix
`--debug-mode ` (two hyphens, `debug-mode`, one space). Do not recognize a
leading-space, embedded, or otherwise altered spelling as the prefix. After
recognizing it:

1. Start a report before selecting an operation.
2. Remove the prefix and the one separating space from the request.
3. Route and execute the remaining request through the ordinary SelfContext
   procedure, unchanged.
4. Use the diagnostic helper for known SelfContext scripts when practical.
5. Append visible failures and retries with fixed event codes and safe numeric
   or boolean fields only.
6. Append `session-completed` with `status: complete` before the final response,
   or `session-incomplete` with `status: partial`/`failed` when execution stops.
7. Tell the user the report location separately; never read the report back into
   context unless the user explicitly requests project-maintenance diagnosis.

A normal prompt never invokes the helper and creates no diagnostic file. Do not
promise capture of hidden provider behavior, suppressed harness internals, or
events that are not observable to the agent.

## Privacy contract

Reports are **safe operational metadata, not sanitized transcripts**. Privacy is
provided by a strict allowlist: sensitive bytes never enter the report, so the
helper does not capture and then redact prompts, vault data, command output, or
exception text.

A report may contain only these fixed fields:

- Header: `format_version`, generated random `session_id`, UTC `started_at`, a
  validated repository commit SHA or `unknown`, generated `python_version`,
  platform enum, and harness enum.
- Events: generated UTC `timestamp`; `event`, `component`, `phase`, and
  `operation` enums; bounded `attempt`, `exit_code`, `duration_ms`, retry and
  failure counts; allowlisted finding counts; receipt outcome booleans; and
  `status` enum.
- Finding-count keys: `backup`, `contract`, `filesystem`, `freshness`, `link`,
  `metadata`, `ownership`, `provenance`, `reachability`, `runtime`, `schema`,
  `transaction`, or `unknown`.

The report never contains prompts or prompt-derived values; user text; vault
content, metadata, paths, filenames, links, sources, search terms, results, or
summaries; repository, home, username, or absolute paths; raw commands, argv,
stdout, stderr, tool input/output, proposal bytes, exception/traceback text,
validation messages, finding paths/messages, URLs, secrets, credentials,
tokens, or model/provider identifiers. Vertical or domain scope is not
recorded. Unsupported fields and values are rejected rather than serialized.

## Destination and format

The helper writes
`self-context-debug-<UTC timestamp>-<random session id>.md` under
`~/Downloads` by default. `SELF_CONTEXT_DEBUG_DIR` is the only supported
override. It must be non-empty, resolvable, and outside the tracked repository,
`vault/`, `backups/`, and other canonical SelfContext locations. The path is
never written into the report. The helper creates the report at session start,
appends each event with a flush/sync boundary, and applies owner-only file
permissions (and directory permissions when it creates the output directory)
where the platform supports them. A report containing
only its header and `session-started` event is a useful partial report if the
agent is interrupted. No finish operation rewrites or removes earlier events.

The output directory is validated before any wrapped SelfContext script runs.
If a valid destination cannot be established, the helper fails visibly and the
normal vault operation is not started. Diagnostic-output failure never performs
or rolls back a vault mutation.

## Fixed catalogs

### Components

`backup-vault`, `lint-vault`, `migrate-vault`, `ordinary-commit`,
`prepare-context`, `recent-log`, `search-log`, `search-vault`, `sync-indexes`,
`diagnostic-helper`, and `harness`.

### Operations

`query`, `ingest`, `checkpoint`, `lint`, `review`, `upgrade`, `migration`,
`deep-maintenance`, `advisor`, and `unknown`.

### Phases

`session`, `preflight`, `context-preparation`, `retrieval`,
`semantic-processing`, `proposal`, `validation`, `transaction`, `rollback`,
`backup`, `response`, `harness`, and `unknown`.

### Events

| Event | Meaning |
| --- | --- |
| `session-started` | The incremental report was created. |
| `session-completed` | The overlay reached the final response boundary. |
| `session-incomplete` | Execution stopped before a normal final response. |
| `script-started` | A mapped SelfContext helper was invoked. |
| `script-succeeded` | A mapped helper returned exit code zero. |
| `script-failed` | A mapped helper returned a non-zero exit code. |
| `script-timeout` | A mapped helper exceeded its bounded timeout. |
| `tool-input-rejected` | A visible tool input failed a documented contract. |
| `tool-call-failed` | A visible helper/tool call could not run. |
| `edit-mismatch` | A visible anchored edit did not match its expected source. |
| `retry-started` | A visible retry began; use the numeric attempt field. |
| `output-contract-invalid` | Visible helper output failed its expected structure. |
| `unexpected-noop` | A requested observable action produced an unexpected no-op. |
| `unexpected-behavior` | Observable behavior did not fit another fixed event. |
| `receipt-failed` | A visible receipt could not be produced or checked. |
| `validation-failed` | A visible validation step failed. |
| `rollback-failed` | A visible rollback step failed. |
| `backup-failed` | A visible backup step failed. |

`status` is one of `complete`, `partial`, `failed`, or `unknown`. A completed
session uses `session-completed`; all other finish statuses use
`session-incomplete`.

## Helper commands

Run from the repository root. The helper is not a generic command runner:
`run` accepts only the mapped components above, constructs the known Python
script command, does not use `shell=True`, and lets the script inherit normal
stdout/stderr. It records only component, phase, operation, attempt, duration,
exit code, and the fixed script event.

```text
python3 .agents/skills/self-context/scripts/debug_diagnostics.py start
python3 .agents/skills/self-context/scripts/debug_diagnostics.py run \
  --report "$DEBUG_REPORT" \
  --component prepare-context \
  --phase context-preparation \
  --operation query \
  -- <known prepare_context.py arguments>
python3 .agents/skills/self-context/scripts/debug_diagnostics.py finish \
  --report "$DEBUG_REPORT" \
  --status complete \
  --operation query
```

For a visible failure outside the wrapper, append only a fixed event, for
example:

```text
python3 .agents/skills/self-context/scripts/debug_diagnostics.py event \
  --report "$DEBUG_REPORT" \
  --event tool-call-failed \
  --component harness \
  --phase response \
  --operation query \
  --attempt 1
```

Never add a free-text event option. Preserve ordinary SelfContext receipt,
backup, rollback, validation, and response behavior; the overlay observes
those outcomes rather than replacing their owners. Never ingest, index, back
up, migrate, or retrieve a report; never create a vault operation-log entry,
improvement backlog, or tracked project change for it.
