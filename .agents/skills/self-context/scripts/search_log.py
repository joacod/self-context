#!/usr/bin/env python3
"""Search older SelfContext operation history without emitting the full log."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from log_utils import (
        DEFAULT_LOG_LIMIT,
        LogMatch,
        LogReadError,
        operation_log_path,
        search_log_entries,
    )
except ImportError:  # pragma: no cover
    from .log_utils import (  # type: ignore
        DEFAULT_LOG_LIMIT,
        LogMatch,
        LogReadError,
        operation_log_path,
        search_log_entries,
    )


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from error
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def search_log(vault: Path, query: str, limit: int = DEFAULT_LOG_LIMIT) -> List[LogMatch]:
    """Return bounded, ranked complete entries matching *query*."""

    return search_log_entries(operation_log_path(vault), query, limit=limit)


def _match_record(match: LogMatch) -> Dict[str, Any]:
    entry = match.entry
    return {
        "date": entry.date,
        "operation": entry.operation,
        "heading": entry.heading,
        "text": entry.text,
        "score": match.score,
        "matched_terms": list(match.matched_terms),
        "query_term_coverage": match.query_term_coverage,
    }


def _print_text(matches: List[LogMatch]) -> None:
    if not matches:
        print("No matching operation log entries")
        return
    for index, match in enumerate(matches):
        text = match.entry.text
        print(text, end="" if text.endswith(("\n", "\r")) else "\n")
        if index + 1 < len(matches) and not text.endswith(("\n\n", "\r\n\r\n")):
            print()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Search complete operation entries in log.md with bounded lexical "
            "results; use for explicit historical lookup"
        )
    )
    parser.add_argument("query", help="terms to find in operation entries")
    parser.add_argument("vault", nargs="?", default="vault")
    parser.add_argument(
        "--limit",
        type=_non_negative_int,
        default=DEFAULT_LOG_LIMIT,
        help=f"maximum matching entries to print (default: {DEFAULT_LOG_LIMIT})",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        matches = search_log(Path(args.vault), args.query, limit=args.limit)
    except (LogReadError, OSError, UnicodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(
            json.dumps(
                {
                    "query": args.query,
                    "limit": args.limit,
                    "matches": [_match_record(match) for match in matches],
                },
                indent=2,
            )
        )
    else:
        _print_text(matches)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
