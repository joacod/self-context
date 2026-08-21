#!/usr/bin/env python3
"""Print a bounded recent slice of a SelfContext operation log."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from log_utils import (
        DEFAULT_LOG_LIMIT,
        LogEntry,
        LogReadError,
        operation_log_path,
        read_recent_entries,
    )
except ImportError:  # pragma: no cover
    from .log_utils import (  # type: ignore
        DEFAULT_LOG_LIMIT,
        LogEntry,
        LogReadError,
        operation_log_path,
        read_recent_entries,
    )


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from error
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def _entry_record(entry: LogEntry) -> Dict[str, Any]:
    return {
        "heading": entry.heading,
        "date": entry.date,
        "operation": entry.operation,
        "text": entry.text,
    }


def recent_log(vault: Path, entries: int = DEFAULT_LOG_LIMIT) -> List[LogEntry]:
    """Return the bounded recent operation entries for *vault*."""

    return read_recent_entries(operation_log_path(vault), limit=entries)


def _print_text(entries: List[LogEntry]) -> None:
    if not entries:
        print("No operation log entries")
        return
    for entry in entries:
        text = entry.text
        print(text, end="" if text.endswith(("\n", "\r")) else "\n")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print only the newest complete operation entries from log.md"
    )
    parser.add_argument("vault", nargs="?", default="vault")
    parser.add_argument(
        "--entries",
        type=_non_negative_int,
        default=DEFAULT_LOG_LIMIT,
        help=f"maximum complete entries to print (default: {DEFAULT_LOG_LIMIT})",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        entries = recent_log(Path(args.vault), entries=args.entries)
    except (LogReadError, OSError, UnicodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps({"entries": [_entry_record(entry) for entry in entries]}, indent=2))
    else:
        _print_text(entries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
