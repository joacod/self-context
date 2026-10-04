# Fictional context evaluation

Use this workflow to assess agent behavior separately from deterministic tests.
All cases use fictional John Doe data in isolated temporary projects. The runner
prepares cases and checks file effects; it neither calls a model nor decides
whether an answer is semantically correct.

## Run a trial

From the repository root, choose a **new** temporary directory:

```bash
python3 scripts/evaluate_context.py prepare /tmp/selfcontext-evaluation-trial-1
```

The command refuses an existing destination. Each case has its own `vault/`,
`prompt.txt`, and before-state hashes. Cases cover exact, paraphrased and accented
retrieval, successors, freshness, counterevidence, corrections, partial
confirmation, re-ingestion, checkpoint rejection, temporal evidence, and partial
supersession. The expectations live in `scripts/evaluate_context.py`; fixture
construction lives in `tests/context_scenarios.py`.

1. Set the actual model, harness/version, settings and repetition in `run.json`.
   Record unavailable details as unavailable, not guessed versions.
2. Give the evaluating agent the project-local SelfContext skill and one case's
   `prompt.txt`, with its explicit temporary vault path. For an independent
   trial, keep expectations and other cases out of its input. Run cases in fresh
   contexts. Do not use the production vault or enable verticals to satisfy a
   retrieval miss.
3. Capture actual tool calls and outputs in a case-local `trace.json` or another
   recorded trace. Complete evidence already returned counts as a read. Source
   metadata alone does not. Mutations must use the ordinary snapshot, backup,
   validation and receipt lifecycle. Save receipts separately from the vault.
4. Save `response.json` with `answer` (string), `evidence_paths` (paths actually
   used), and `retrieval_calls` (integer). These metrics are self-reported until
   checked against the trace.
5. Review answers and traces against the case's `review` rubric and save
   `review.json`, for example:

   ```json
   {"reviewer": "independent reviewer", "result": "pass", "notes": "No unsupported claims; confirmation stayed scoped."}
   ```

6. Run the mechanical checker:

   ```bash
   python3 scripts/evaluate_context.py check /tmp/selfcontext-evaluation-trial-1
   ```

A zero exit status means responses exist and mechanical checks passed. It does
**not** mean semantic review passed. Inspect `semantic_review`, evidence recall,
read counts, support for every answer claim, freshness qualifications, and
mutation contents. The checker detects writes outside each allowlist, absent
required mutations, selected metadata errors, and backups from read-only/no-op
cases. Allowlisted changes still need content review. It does not monitor
arbitrary writes outside the disposable projects or verify a model's claims
about its own trace. Repeat in a new directory; never recycle mutated cases.

No model service or paid API is required. Separately authorize any external
model execution. CI runs deterministic fixture/checker tests only.

## Pass 2 observation, 2026-10-03

The [recorded results](evaluations/context-pass2-2026-10-03.json) contain one
**guided, scenario-aware self-review** in the implementation session, not an
independent model benchmark. The harness was Codex desktop; the exact served
model version and settings were unavailable. Expectations were visible and
retrieval anchors were deliberately selected from them. This establishes that
the procedures and tools can support the cases; it does not measure how often
an unassisted agent chooses the right anchors or follows the procedures.

All 12 mechanical outcomes passed. Three mutations completed through ordinary
commit; the other nine cases left their vault bytes unchanged. All 11 cases
requiring evidence returned their expected paths as complete evidence. The
English paraphrase required two calls (one scoped Spanish reformulation); the
counterevidence case required two calls (one justified review lookup); the
checkpoint case required none. The others required one call. There were nine
additional returned page occurrences beyond expected evidence across the trial,
mostly weaker lexical candidates; evidence recall alone therefore overstates
retrieval precision. No semantic accuracy percentage is claimed.

The English query alone missed the Spanish page, while the bounded translated
retry found it. Accentless Spanish worked directly. The freshness answer kept
an expired role historical. The review qualification stayed an inference, and
partial changes did not verify unrelated claims. Independent repeated trials
remain the way to assess behavioral reliability; they are an optional evaluation
activity, not an unimplemented runtime component.
