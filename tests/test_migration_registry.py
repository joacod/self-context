from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"


class MigrationRegistryTests(unittest.TestCase):
    def test_registry_and_schema_helpers_are_independent_of_migration_engine(self) -> None:
        script = f"""
import sys
sys.path.insert(0, {str(SCRIPTS)!r})
import migration_registry
import vault_utils

assert \"migrate_vault\" not in sys.modules
assert migration_registry.default_migration_registry().latest_supported_schema == \"0.2\"
assert migration_registry.default_migration_registry().supported_versions == [\"0.1\", \"0.2\"]
assert vault_utils.latest_schema_version() == \"0.2\"
assert vault_utils.supported_schema_versions() == [\"0.1\", \"0.2\"]
assert \"migrate_vault\" not in sys.modules
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_default_topology_resolves_path_without_executable_planner(self) -> None:
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        import migration_registry  # type: ignore

        registry = migration_registry.default_migration_registry()
        self.assertIsNone(registry.edges[0].planner)
        self.assertEqual(
            [edge.label for edge in registry.resolve_path("0.1", "latest")],
            ["0.1->0.2"],
        )
        self.assertEqual(registry.validation_findings(), [])


    def test_migration_engine_binds_historical_planner(self) -> None:
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        if str(ROOT / "tests") not in sys.path:
            sys.path.insert(0, str(ROOT / "tests"))
        import migration_registry  # type: ignore
        import migrate_vault  # type: ignore
        from synthetic_vault import build_synthetic_vault  # type: ignore

        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary), schema_version="0.1")
            registry = migration_registry.default_migration_registry()
            self.assertIsNone(registry.edges[0].planner)

            result = migrate_vault.apply_migration(vault, registry=registry)

            self.assertEqual(result["status"], "success")
            self.assertIs(
                registry.edges[0].planner,
                migrate_vault._plan_0_1_to_0_2,
            )
            self.assertEqual(result["migration_path"], ["0.1", "0.2"])


if __name__ == "__main__":
    unittest.main()
