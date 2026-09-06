from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import validate_json
import validate_repo


class RepositoryValidatorTests(unittest.TestCase):
    def run_validator(self, directory: Path) -> tuple[int, str]:
        output = io.StringIO()
        with (
            mock.patch.object(validate_repo, 'TESTS_DIR', directory),
            mock.patch.object(validate_repo, 'validate_skill_metadata', return_value=([], [], [])),
            mock.patch.object(validate_repo, 'validate_tracked_json', return_value=[]) as json_check,
            contextlib.redirect_stdout(output),
        ):
            status = validate_repo.main()
        json_check.assert_called_once_with(validate_repo.ROOT)
        return status, output.getvalue()

    def test_empty_discovery_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            status, output = self.run_validator(Path(temporary))
        self.assertEqual(status, 1)
        self.assertIn('test discovery found no cases', output)

    def test_import_error_fails_discovery_and_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'test_broken_validator_fixture.py').write_text("raise RuntimeError('synthetic import failure')\n")
            status, output = self.run_validator(directory)
        self.assertEqual(status, 1)
        self.assertIn('[FAIL] test discovery:', output)
        self.assertIn('synthetic import failure', output)
        self.assertIn('1 error(s)', output)

    def test_json_validation_runs_when_discovery_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(unittest.TestLoader, 'discover', side_effect=RuntimeError('synthetic discovery failure')):
                status, output = self.run_validator(Path(temporary))
        self.assertEqual(status, 1)
        self.assertIn('test discovery failed: RuntimeError', output)
        self.assertIn('[PASS] tracked JSON parsed', output)

    def test_loader_errors_cannot_be_hidden_by_a_successful_suite(self) -> None:
        loader = unittest.TestLoader()
        loader.errors.append('synthetic load_tests failure')
        with tempfile.TemporaryDirectory() as temporary:
            with (
                mock.patch.object(validate_repo.unittest, 'TestLoader', return_value=loader),
                mock.patch.object(loader, 'discover', return_value=unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])),
            ):
                status, output = self.run_validator(Path(temporary))
        self.assertEqual(status, 1)
        self.assertIn('synthetic load_tests failure', output)

    def test_suppressed_execution_fails_count_check(self) -> None:
        class SuppressedTest(unittest.TestCase):
            def run(self, result=None):
                return result

        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(unittest.TestLoader, 'discover', return_value=unittest.TestSuite([SuppressedTest()])):
                status, output = self.run_validator(Path(temporary))
        self.assertEqual(status, 1)
        self.assertIn('unittest executed 0 of 1 discovered cases', output)

    def test_ordinary_failure_fails_validation(self) -> None:
        def fail():
            raise AssertionError('synthetic assertion failure')

        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(unittest.TestLoader, 'discover', return_value=unittest.TestSuite([unittest.FunctionTestCase(fail)])):
                status, output = self.run_validator(Path(temporary))
        self.assertEqual(status, 1)
        self.assertIn('1 failure(s) and 0 error(s)', output)

    def test_small_successful_discovery_has_no_fixed_floor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'test_successful_validator_fixture.py').write_text(
                'import unittest\nclass SyntheticTest(unittest.TestCase):\n'
                '    def test_ok(self):\n        self.assertEqual(2 + 2, 4)\n'
            )
            status, output = self.run_validator(directory)
        self.assertEqual(status, 0, output)
        self.assertIn('unittest execution: 1 cases started', output)

    def test_tracked_json_failure_is_independent_of_successful_tests(self) -> None:
        output = io.StringIO()
        with (
            mock.patch.object(validate_repo, 'validate_skill_metadata', return_value=([], [], [])),
            mock.patch.object(validate_repo, 'validate_tracked_json', return_value=['synthetic.json: invalid JSON']) as check,
            mock.patch.object(unittest.TestLoader, 'discover', return_value=unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(validate_repo.main(), 1)
        check.assert_called_once_with(validate_repo.ROOT)
        self.assertIn('synthetic.json: invalid JSON', output.getvalue())

    def test_json_cli_enumerates_once_and_rejects_non_json_constants(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'synthetic.json'
            path.write_text('{"invalid": NaN}')
            with mock.patch.object(validate_json, 'tracked_json_paths', return_value=[path]) as enumerate_paths:
                problems = validate_json.validate_tracked_json(path.parent)
            enumerate_paths.assert_called_once_with(path.parent)
            self.assertEqual(problems, ['synthetic.json: invalid JSON constant: NaN'])
            path.write_text('{"valid": true}')
            validate = validate_json.validate_tracked_json
            with (
                mock.patch.object(validate_json, 'tracked_json_paths', return_value=[path]) as enumerate_paths,
                mock.patch.object(validate_json, 'validate_tracked_json', side_effect=lambda: validate(path.parent)),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(validate_json.main(), 0)
            enumerate_paths.assert_called_once_with(path.parent)


if __name__ == '__main__':
    unittest.main()
