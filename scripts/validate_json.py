#!/usr/bin/env python3
"""Validate every tracked JSON file without third-party dependencies."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parents[1]


def tracked_json_paths(root: Path = ROOT) -> List[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.json"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace").strip()
        raise RuntimeError(detail or "git ls-files failed")
    return [
        root / Path(os.fsdecode(raw_path))
        for raw_path in result.stdout.split(b"\0")
        if raw_path
    ]


def reject_non_json_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def validate_tracked_json(root: Path = ROOT) -> List[str]:
    problems: List[str] = []
    for path in tracked_json_paths(root):
        label = path.relative_to(root).as_posix()
        try:
            with path.open(encoding="utf-8") as handle:
                json.load(handle, parse_constant=reject_non_json_constant)
        except json.JSONDecodeError as error:
            problems.append(
                f"{label}: line {error.lineno}, column {error.colno}: {error.msg}"
            )
        except (OSError, UnicodeError, ValueError) as error:
            problems.append(f"{label}: {error}")
    return problems


def main() -> int:
    try:
        paths = tracked_json_paths()
        problems = validate_tracked_json()
    except Exception as error:
        print(f"[FAIL] tracked JSON validation failed: {type(error).__name__}: {error}")
        return 1

    if problems:
        for problem in problems:
            print(f"[FAIL] tracked JSON: {problem}")
        return 1
    print(f"[PASS] tracked JSON: {len(paths)} files parsed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
