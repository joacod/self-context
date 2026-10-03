#!/usr/bin/env python3
"""Measure context preparation and commits using temporary fictional vaults only."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT / "tests", ROOT / ".agents/skills/self-context/scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import ordinary_commit
import prepare_context
import sync_indexes
from synthetic_vault import build_synthetic_vault, write_page


def positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def benchmark(pages: int, repetitions: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="selfcontext-benchmark-") as temporary:
        vault = build_synthetic_vault(Path(temporary))
        for number in range(pages):
            write_page(
                vault, f"career/scale-{number:04}.md",
                title=f"John Doe delivery example {number}",
                body=("John Doe delivered release planning for MyContext Systems. "
                      "Evidence includes careful technical decisions and team coordination.\n") * 15,
            )
        sync_indexes.synchronize(vault, write=True)
        timings: dict[str, list[float]] = {
            name: [] for name in ("query", "mutation_preparation", "noop", "commit")
        }
        packet_bytes = 0
        for revision in range(repetitions):
            options = dict(
                scope=["career"],
                anchors=["delivery planning", "technical decisions", "team coordination"],
                include_evidence=True,
            )
            start = time.perf_counter()
            packet = prepare_context.prepare_context(vault, **options)
            timings["query"].append(time.perf_counter() - start)
            packet_bytes = len(json.dumps(packet).encode("utf-8"))
            start = time.perf_counter()
            mutation = prepare_context.prepare_context(vault, for_update=True, **options)
            timings["mutation_preparation"].append(time.perf_counter() - start)
            if not mutation["controls"]["mutation_ready"]:
                raise RuntimeError("synthetic mutation preparation failed")
            label = "career/scale-0000.md"
            content = (vault / label).read_text()
            proposal = {
                "expected_snapshot": mutation["controls"]["expected_snapshot"],
                "writes": {label: content},
            }
            start = time.perf_counter()
            noop = ordinary_commit.commit_mutation(vault, proposal)
            timings["noop"].append(time.perf_counter() - start)
            if noop["status"] != "noop":
                raise RuntimeError(f"synthetic no-op failed: {noop['state']}")
            proposal["writes"] = {label: content + f"\nFictional revision {revision}.\n"}
            proposal["log"] = {
                "operation": "ingest", "summary": "Update fictional evidence", "paths": [label],
            }
            start = time.perf_counter()
            result = ordinary_commit.commit_mutation(vault, proposal)
            timings["commit"].append(time.perf_counter() - start)
            if result["status"] != "success":
                raise RuntimeError(f"synthetic commit failed: {result['state']}")
        return {
            "extra_pages": pages, "repetitions": repetitions,
            "query_packet_bytes": packet_bytes,
            "median_seconds": {name: statistics.median(values) for name, values in timings.items()},
            "runs_seconds": timings,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", type=positive, nargs="+", default=[100, 500])
    parser.add_argument("--repetitions", type=positive, default=3)
    args = parser.parse_args()
    print(json.dumps({"python": sys.version, "platform": sys.platform, "profiled": False}))
    for pages in args.pages:
        print(json.dumps(benchmark(pages, args.repetitions)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
