#!/usr/bin/env python3
"""Run the repository's dependency-free validation checks.

The test floor is intentionally below the current discovered count so small,
platform-specific changes do not make the check brittle. It is still high
enough to catch a discovery failure such as the deep-lint TestCase lifecycle
collision that reduced execution from 43 discovered cases to 35.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Iterable, List, Tuple

try:
    from validate_json import validate_tracked_json as _validate_tracked_json
except ImportError:  # pragma: no cover - package-style import fallback
    from .validate_json import validate_tracked_json as _validate_tracked_json  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
TEST_PATTERN = "test_*.py"
CURRENT_EXPECTED_TESTS = 113
MIN_EXPECTED_TESTS = 40
EXPECTED_DEEP_LINT_TESTS = 15


class RecordingTextTestResult(unittest.TextTestResult):
    """Keep the normal unittest report while recording which cases started."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.started_test_ids: List[str] = []

    def startTest(self, test: unittest.case.TestCase) -> None:
        self.started_test_ids.append(test.id())
        super().startTest(test)


def iter_test_cases(suite: unittest.TestSuite) -> Iterable[unittest.case.TestCase]:
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from iter_test_cases(test)
        else:
            yield test


def discover_tests() -> Tuple[unittest.TestSuite, List[unittest.case.TestCase]]:
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(TESTS_DIR),
        pattern=TEST_PATTERN,
    )
    return suite, list(iter_test_cases(suite))


def validate_tracked_json() -> List[str]:
    problems = _validate_tracked_json(ROOT)
    if problems:
        for problem in problems:
            print(f"[FAIL] tracked JSON: {problem}")
    else:
        # Keep the canonical validator's existing output stable while the
        # standalone JSON gate is also usable by CI.
        print(f"[PASS] tracked JSON: {len(_tracked_json_paths())} files parsed")
    return problems


def _tracked_json_paths() -> List[Path]:
    """Return the same tracked set for the canonical summary line."""

    import validate_json

    return validate_json.tracked_json_paths(ROOT)


def main() -> int:
    problems: List[str] = []
    suite: unittest.TestSuite | None = None
    discovered: List[unittest.case.TestCase] = []

    try:
        suite, discovered = discover_tests()
    except Exception as error:  # discovery/import errors must fail validation
        message = f"test discovery failed: {type(error).__name__}: {error}"
        print(f"[FAIL] {message}")
        problems.append(message)

    if suite is not None:
        discovered_count = len(discovered)
        print(
            f"[PASS] test discovery: {discovered_count} cases found "
            f"(minimum {MIN_EXPECTED_TESTS}; current expected {CURRENT_EXPECTED_TESTS})"
            if discovered_count >= MIN_EXPECTED_TESTS
            else
            f"[FAIL] test discovery: {discovered_count} cases found; "
            f"need at least {MIN_EXPECTED_TESTS}"
        )
        if discovered_count < MIN_EXPECTED_TESTS:
            problems.append(
                f"discovered test count {discovered_count} is below the "
                f"conservative minimum {MIN_EXPECTED_TESTS}"
            )

        deep_lint_ids = sorted(
            test.id()
            for test in discovered
            if test.id().startswith("test_deep_lint.DeepLintTests.test_")
        )
        if len(deep_lint_ids) < EXPECTED_DEEP_LINT_TESTS:
            message = (
                f"deep-lint discovery found {len(deep_lint_ids)} cases; "
                f"need at least {EXPECTED_DEEP_LINT_TESTS}"
            )
            print(f"[FAIL] {message}")
            problems.append(message)
        else:
            print(f"[PASS] deep-lint discovery: {len(deep_lint_ids)} cases found")

        try:
            problems.extend(validate_tracked_json())
        except Exception as error:
            message = f"tracked JSON validation failed: {type(error).__name__}: {error}"
            print(f"[FAIL] {message}")
            problems.append(message)

        try:
            runner = unittest.TextTestRunner(
                stream=sys.stdout,
                verbosity=1,
                resultclass=RecordingTextTestResult,
            )
            result = runner.run(suite)
            executed_count = result.testsRun
            if executed_count != discovered_count:
                message = (
                    f"unittest executed {executed_count} of "
                    f"{discovered_count} discovered cases"
                )
                print(f"[FAIL] {message}")
                problems.append(message)
            else:
                print(f"[PASS] unittest execution: {executed_count} cases started")

            missing_deep_lint = sorted(
                set(deep_lint_ids) - set(result.started_test_ids)
            )
            if missing_deep_lint:
                message = "deep-lint cases were discovered but not executed: " + ", ".join(
                    missing_deep_lint
                )
                print(f"[FAIL] {message}")
                problems.append(message)

            if not result.wasSuccessful():
                message = (
                    f"unittest reported {len(result.failures)} failure(s) and "
                    f"{len(result.errors)} error(s)"
                )
                print(f"[FAIL] {message}")
                problems.append(message)
            else:
                print(
                    f"[PASS] unittest results: {len(result.skipped)} skipped, "
                    "0 failures, 0 errors"
                )
        except Exception as error:  # runner failures are validation failures
            message = f"unittest execution failed: {type(error).__name__}: {error}"
            print(f"[FAIL] {message}")
            problems.append(message)
    else:
        # JSON validation remains useful even when test discovery cannot start.
        try:
            problems.extend(validate_tracked_json())
        except Exception as error:
            message = f"tracked JSON validation failed: {type(error).__name__}: {error}"
            print(f"[FAIL] {message}")
            problems.append(message)

    if problems:
        print(f"Repository validation failed ({len(problems)} issue(s)).")
        return 1

    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
