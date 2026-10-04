#!/usr/bin/env python3
"""Prepare fictional agent evaluations and check outcomes; never call a model."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT / "tests", ROOT / ".agents/skills/self-context/scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import vault_utils
from context_scenarios import build_context_scenarios

CASES = [
    {"id": "exact", "prompt": "What technical leadership evidence does John Doe have? Search for Liderazgo técnico. Answer without saving anything.",
     "evidence": ["career/leadership.md"], "review": "Attribute the source-derived migration evidence; do not invent outcomes."},
    {"id": "paraphrase", "prompt": "What experience does John Doe have directing technical work? The retained evidence may be in Spanish. Just answer.",
     "evidence": ["career/leadership.md"], "review": "Use at most one bounded reformulation pass, not global search or a new alias write."},
    {"id": "accent", "prompt": "Que evidencia hay de liderazgo tecnico de John Doe? No guardes nada.",
     "evidence": ["career/leadership.md"], "review": "Answer in Spanish with provenance; a folded lexical hit is not an exact identity claim."},
    {"id": "successor", "prompt": "What does John's expansion decision say now? Do not save the answer.",
     "evidence": ["career/expansion-old.md", "career/maintenance.md"], "review": "Distinguish the previous expansion plan from maintenance; do not claim expansion is current."},
    {"id": "freshness", "prompt": "As of 2026-10-03, what is John's current role? Just answer from the vault.",
     "evidence": ["career/current-role.md"], "review": "Report historical coverage and expired freshness; currentness needs confirmation."},
    {"id": "counterevidence", "prompt": "Help John decide whether to expand now, based on the recorded decision and availability. Keep this ephemeral.",
     "evidence": ["career/maintenance.md", "core/availability.md", "review/observations/expansion-constraint.md"],
     "review": "Check the review qualification without turning an inference into a fact; recommendation remains derived."},
    {"id": "correction", "prompt": "On 2026-10-03 John corrects his weekly availability to three days and explicitly confirms that availability claim. Update only its existing page and preserve provenance.",
     "evidence": ["core/availability.md"], "writes": ["core/availability.md", "core/index.md", "log.md"],
     "fields": {"core/availability.md": {"verified": "2026-10-03", "assertion_kind": "user_stated_fact"}},
     "review": "Three days replaces the current availability; preserve dated historical context. No unrelated confirmation."},
    {"id": "partial-confirmation", "prompt": "On 2026-10-03 John explicitly confirms only that he works remotely. Confirm the remote-work page; do not confirm any availability claim.",
     "evidence": ["core/remote-work.md"], "writes": ["core/remote-work.md", "core/index.md", "review/index.md", "log.md"],
     "fields": {"core/remote-work.md": {"verified": "2026-10-03", "status": "active"}},
     "review": "Availability and the composite work-arrangement page must remain byte-identical."},
    {"id": "reingest", "prompt": "Record this again if needed: as of 2026-08-12 John reported two days a week for projects. It is the same evidence already retained, not a new confirmation or freshness update.",
     "evidence": ["core/availability.md"], "review": "No duplicate page/source, verification renewal, log, or backup for unchanged context."},
    {"id": "checkpoint", "prompt": "Checkpoint this fictional discussion: assistant suggested John prefers mornings; John replied 'that is only a hypothesis, do not save it.' Nothing else was decided.",
     "evidence": [], "review": "Retain nothing; do not turn the assistant suggestion into a user preference or review item."},
    {"id": "temporal", "prompt": "Compare the dates of John's role and availability evidence. Does either establish the other as current? Just answer.",
     "evidence": ["career/current-role.md", "core/availability.md"], "review": "Separate event/as-of dates, generated dates, verification, and deadlines. Unknowns remain unknown."},
    {"id": "partial-supersession", "prompt": "John reports on 2026-10-03 that only the Availability section of the work-arrangement page changed from two days to three. Update that section with dated evolution; he is not confirming the rest of the page.",
     "evidence": ["core/work-arrangement.md"], "writes": ["core/work-arrangement.md", "core/index.md", "log.md"],
     "fields": {"core/work-arrangement.md": {"verified": None}},
     "review": "Keep remote-work wording and sources intact, retain dated availability history, and do not mark the whole page verified."},
]


def hashes(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("evaluation trees must not contain symlinks")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def prepare(destination: Path) -> None:
    # Refuse existing roots: this command cannot initialize or overwrite a live vault.
    destination.mkdir(parents=True, exist_ok=False)
    for case in CASES:
        project = destination / case["id"]
        vault = build_context_scenarios(project)
        (project / "prompt.txt").write_text(
            f"Use the project-local SelfContext skill with this explicitly supplied synthetic vault: {vault.resolve()}\n"
            f"Evaluation date: 2026-10-03.\n\n{case['prompt']}\n", encoding="utf-8"
        )
        (project / "before.json").write_text(json.dumps(hashes(vault), sort_keys=True))
    (destination / "run.json").write_text(json.dumps({
        "format": "selfcontext-fictional-eval-1", "model": None, "harness": None,
        "settings": None, "repetition": 1,
    }, indent=2))


def check(destination: Path) -> dict:
    metadata = json.loads((destination / "run.json").read_text())
    if metadata.get("format") != "selfcontext-fictional-eval-1":
        raise ValueError("not an evaluation run")
    outcomes = []
    for case in CASES:
        project = destination / case["id"]
        before = json.loads((project / "before.json").read_text())
        after = hashes(project / "vault")
        changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
        unexpected = sorted(set(changed) - set(case.get("writes", [])))
        errors = []
        for label, fields in case.get("fields", {}).items():
            actual = vault_utils.page_record(project / "vault" / label, project / "vault").get("frontmatter", {})
            for key, value in fields.items():
                if actual.get(key) != value:
                    errors.append(f"{label}: unexpected {key}")
        if case.get("writes") and not changed:
            errors.append("expected mutation was not applied")
        if not case.get("writes") and list((project / "backups").glob("*")):
            errors.append("read-only/no-op case created backups")
        response_path = project / "response.json"
        response = json.loads(response_path.read_text()) if response_path.exists() else {}
        evidence = set(response.get("evidence_paths", []))
        expected = set(case["evidence"])
        review_path = project / "review.json"
        review = json.loads(review_path.read_text()) if review_path.exists() else None
        outcomes.append({
            "id": case["id"], "responded": bool(response.get("answer")),
            "mechanical_ok": not unexpected and not errors, "changed": changed,
            "unexpected_writes": unexpected, "errors": errors,
            "evidence_recall_reported": len(expected & evidence) / len(expected) if expected else None,
            "retrieval_calls_reported": response.get("retrieval_calls"),
            "review_criterion": case["review"], "semantic_review": review,
        })
    return {"run": metadata, "outcomes": outcomes,
            "note": "Mechanical checks and self-reported retrieval metrics do not prove semantic correctness. Review answers and traces separately."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "check"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.operation == "prepare":
        prepare(args.directory)
        print(f"Prepared {len(CASES)} fictional cases in {args.directory}")
        return 0
    report = check(args.directory)
    print(json.dumps(report, indent=2))
    return 0 if all(o["mechanical_ok"] and o["responded"] for o in report["outcomes"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
