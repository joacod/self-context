#!/usr/bin/env python3
"""Run the repository's dependency-free validation checks."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

try:
    from validate_json import validate_tracked_json
    from validate_skill_metadata import validate_skill_metadata
except ImportError:  # pragma: no cover - package-style import fallback
    from .validate_json import validate_tracked_json
    from .validate_skill_metadata import validate_skill_metadata


ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
TEST_PATTERN = "test_*.py"


def main() -> int:
    problems: list[str] = []

    def fail(message: str) -> None:
        print(f"[FAIL] {message}")
        problems.append(message)

    try:
        skill_paths, skill_problems, skill_warnings = validate_skill_metadata(ROOT)
        for warning in skill_warnings:
            print(f"[WARN] skill metadata: {warning}")
        for problem in skill_problems:
            fail(f"skill metadata: {problem}")
        if not skill_problems:
            print(f"[PASS] skill metadata: {len(skill_paths)} skill files checked")
    except Exception as error:
        fail(f"skill metadata validation failed: {type(error).__name__}: {error}")

    # JSON validation is independent of discovery and enumerates tracked files once.
    try:
        json_problems = validate_tracked_json(ROOT)
        for problem in json_problems:
            fail(f"tracked JSON: {problem}")
        if not json_problems:
            print("[PASS] tracked JSON parsed")
    except Exception as error:
        fail(f"tracked JSON validation failed: {type(error).__name__}: {error}")

    try:
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir=str(TESTS_DIR), pattern=TEST_PATTERN)
        discovered_count = suite.countTestCases()
        for error in loader.errors:
            fail(f"test discovery: {error}")
        if not discovered_count:
            fail("test discovery found no cases")
        elif not loader.errors:
            print(f"[PASS] test discovery: {discovered_count} cases found")
    except Exception as error:
        fail(f"test discovery failed: {type(error).__name__}: {error}")
    else:
        try:
            result = unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite)
            if result.testsRun != discovered_count:
                fail(
                    f"unittest executed {result.testsRun} of "
                    f"{discovered_count} discovered cases"
                )
            else:
                print(f"[PASS] unittest execution: {result.testsRun} cases started")
            if not result.wasSuccessful():
                fail(
                    f"unittest reported {len(result.failures)} failure(s) and "
                    f"{len(result.errors)} error(s)"
                )
            else:
                print(f"[PASS] unittest results: {len(result.skipped)} skipped, 0 failures, 0 errors")
        except Exception as error:
            fail(f"unittest execution failed: {type(error).__name__}: {error}")

    if problems:
        print(f"Repository validation failed ({len(problems)} issue(s)).")
        return 1
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
