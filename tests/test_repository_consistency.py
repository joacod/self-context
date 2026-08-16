from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents/skills/self-context"
CATALOG_PATH = SKILL_ROOT / "references/verticals.json"

# Keep this guard deliberately narrow: it protects the known legacy fixture
# aliases without prohibiting distinct people, works, or project names needed
# by relationship and media scenarios.
LEGACY_SYNTHETIC_PLACEHOLDER_PATTERNS = (
    ("Nia", re.compile(r"\bNia(?:\s+Vale|'s)?\b")),
    ("Cedar Cooperative", re.compile(r"\bCedar Cooperative\b")),
    ("generic company placeholder", re.compile(r"\bCompany [A-Z]\b")),
)

if str(ROOT / ".agents/skills/self-context/scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / ".agents/skills/self-context/scripts"))

import vault_utils  # type: ignore  # noqa: E402


class RepositoryConsistencyTests(unittest.TestCase):
    """Check stable machine-readable contracts without snapshotting prose."""

    @staticmethod
    def table_rows(path: Path, heading: str) -> list[list[str]]:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        start = lines.index(heading)
        heading_level = len(heading) - len(heading.lstrip("#"))
        rows: list[list[str]] = []
        for line in lines[start + 1 :]:
            heading_match = re.match(r"^(#+)\s+", line)
            if heading_match and len(heading_match.group(1)) <= heading_level:
                break
            if not line.lstrip().startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells and all(set(cell) <= {"-", ":", " "} for cell in cells):
                continue
            rows.append(cells)
        return rows

    @staticmethod
    def routing_rows() -> list[list[str]]:
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        section = text.split("Current vertical routing:", 1)[1].split(
            "- A future vertical", 1
        )[0]
        rows: list[list[str]] = []
        for line in section.splitlines():
            if line.lstrip().startswith("|"):
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if cells and not all(set(cell) <= {"-", ":", " "} for cell in cells):
                    rows.append(cells)
        return rows

    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = vault_utils.load_vertical_catalog(CATALOG_PATH)
        cls.records = vault_utils.catalog_records(cls.catalog)

    def test_catalog_paths_headers_and_advisor_packs_are_consistent(self) -> None:
        self.assertEqual(vault_utils.validate_vertical_catalog(CATALOG_PATH), [])
        self.assertTrue(self.records)
        ids = [str(record["id"]) for record in self.records]
        self.assertEqual(len(ids), len(set(ids)))
        for record in self.records:
            identifier = str(record["id"])
            area = str(record["vault_area"])
            index_path = str(record["index_path"])
            self.assertEqual(index_path, f"{area}/index.md", identifier)
            self.assertFalse(Path(index_path).is_absolute())
            self.assertTrue((SKILL_ROOT / index_path).parent == SKILL_ROOT / area)

            procedure = SKILL_ROOT / str(record["procedure_path"])
            self.assertTrue(procedure.is_file(), identifier)
            header = vault_utils.procedure_header(procedure)
            self.assertEqual(header["vertical_id"], record["id"], identifier)
            self.assertEqual(header["contract_version"], record["contract_version"], identifier)
            self.assertEqual(header["vault_area"], record["vault_area"], identifier)
            self.assertEqual(
                header["advisor_skill"],
                record.get("advisor_skill", record.get("advisor_pack")),
                identifier,
            )

            advisor_pack = record.get("advisor_pack")
            if advisor_pack is not None:
                self.assertTrue(
                    (ROOT / ".agents/skills" / str(advisor_pack) / "SKILL.md").is_file(),
                    identifier,
                )

    def test_intentionally_enumerated_vertical_tables_match_catalog(self) -> None:
        documentation_tables = (
            (ROOT / "README.md", "### Context Areas"),
            (ROOT / "docs/ARCHITECTURE.md", "### Available Vertical Catalog"),
        )
        for path, heading in documentation_tables:
            rows = self.table_rows(path, heading)
            self.assertGreaterEqual(len(rows), len(self.records), path.as_posix())
            for record in self.records:
                display_name = str(record["display_name"])
                area = str(record["vault_area"])
                self.assertTrue(
                    any(
                        row
                        and row[0] == display_name
                        and any(area in cell for cell in row[1:])
                        for row in rows
                    ),
                    f"{path}: {display_name}",
                )

        routing = self.routing_rows()
        for record in self.records:
            self.assertTrue(
                any(row and row[0] == record["display_name"] for row in routing),
                str(record["id"]),
            )

    def test_validation_and_release_commands_are_documented(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        checklist = ROOT / "docs/DEEP_MAINTENANCE_RELEASE_CHECKLIST.md"
        self.assertIn("python3 scripts/validate_repo.py", readme)
        self.assertTrue(checklist.is_file())
        checklist_text = checklist.read_text(encoding="utf-8")
        self.assertIn("python3 scripts/validate_repo.py", checklist_text)

    def test_initialization_preserves_schema_compatibility_and_selective_activation(self) -> None:
        text = (SKILL_ROOT / "references/initialization.md").read_text(encoding="utf-8")
        normalized = " ".join(text.casefold().split())
        self.assertRegex(text, r"schema_version:\s*0\.2")
        self.assertRegex(text, r"vertical_contracts:")
        self.assertRegex(normalized, r"schema\s+0\.1")
        self.assertRegex(normalized, r"schema\s+0\.2")
        self.assertIn("contract markers", normalized)
        self.assertRegex(normalized, r"migration\s+procedure")
        self.assertRegex(normalized, r"does not enable unrelated available\s+verticals")
        self.assertRegex(
            normalized,
            r"never create or enable a vertical for a read-only query, assessment, lint, or\s+review\.",
        )

    def test_deep_maintenance_terminology_keeps_read_only_and_mutating_boundaries(self) -> None:
        text = (SKILL_ROOT / "references/deep-maintenance.md").read_text(encoding="utf-8")
        lowered = text.casefold()
        self.assertIn("deep review", lowered)
        self.assertIn("deep update", lowered)
        self.assertIn("read-only", lowered)
        self.assertIn("pre-write recovery", lowered)
        self.assertIn("post-write backup", lowered)
        self.assertIn("retaining both", lowered)
        self.assertIn("snapshot", lowered)
        self.assertIn("human decisions", lowered)
        self.assertNotRegex(lowered, r"deep review[^.\n]{0,120}\b(?:writes|mutates|creates a backup)\b")
        self.assertNotRegex(lowered, r"deep update[^.\n]{0,120}\b(?:read-only|never writes)\b")

    def test_all_tracked_json_and_eval_files_parse(self) -> None:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", "*.json"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        )
        paths = [
            ROOT / Path(raw.decode())
            for raw in result.stdout.split(b"\0")
            if raw
        ]
        self.assertGreaterEqual(len(paths), 1)
        eval_paths = []
        for path in paths:
            with path.open(encoding="utf-8") as handle:
                parsed = json.load(handle)
            if "/evals/" in path.as_posix():
                eval_paths.append(path)
                if path.name == "evals.json":
                    self.assertIsInstance(parsed, dict)
                    cases = parsed.get("evals")
                    self.assertIsInstance(cases, list)
                    ids = [case.get("id") for case in cases]
                    self.assertEqual(len(ids), len(set(ids)), path.as_posix())
                else:
                    self.assertIsInstance(parsed, list)
        self.assertGreaterEqual(len(eval_paths), 2)

    def test_synthetic_example_placeholders_follow_repository_convention(self) -> None:
        policy_text = "\n".join(
            (
                (ROOT / "AGENTS.md").read_text(encoding="utf-8"),
                (ROOT / "docs/SELF_CONTEXT_SKILL_MAINTENANCE.md").read_text(
                    encoding="utf-8"
                ),
            )
        )
        self.assertIn("John Doe", policy_text)
        self.assertIn("MyContext Systems", policy_text)

        paths = sorted(ROOT.glob(".agents/skills/*/evals/*.json"))
        paths.extend(
            (
                ROOT / "docs/ARCHITECTURE.md",
                SKILL_ROOT / "references/ventures.md",
            )
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for label, pattern in LEGACY_SYNTHETIC_PLACEHOLDER_PATTERNS:
                self.assertIsNone(
                    pattern.search(text),
                    f"legacy synthetic placeholder {label!r} in {path.relative_to(ROOT)}",
                )

    def test_migration_procedure_and_skill_routing_are_canonical(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        procedure_path = SKILL_ROOT / "references/migration.md"
        procedure = procedure_path.read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(procedure_path.is_file())
        self.assertIn("Migrate vault", skill)
        self.assertIn("migrate vault latest", skill.casefold())
        self.assertIn("deep review vault", skill.casefold())
        self.assertIn("deep update vault", skill.casefold())
        self.assertIn("migrate self-context latest", skill.casefold())
        self.assertIn("upgrade vault latest", readme.casefold())
        self.assertNotIn("advanced maintenance prompts include", readme.casefold())
        self.assertIn("references/migration.md", skill)
        self.assertIn("provisional recovery backup", skill.casefold())
        self.assertIn("final backup", skill.casefold())
        self.assertIn("--check", procedure)
        self.assertIn("--write", procedure)
        self.assertIn("--target latest", procedure)
        self.assertIn("pre-write recovery backup", procedure)
        self.assertIn("post-write\n   final-state backup", procedure)
        self.assertIn("sync_indexes.py", procedure)
        self.assertIn("migrate vault latest", procedure.casefold())
        self.assertIn("migrate self-context latest", procedure.casefold())
        self.assertIn("Deep review", procedure)
        self.assertIn("Deep update", procedure)
        self.assertIn("Vertical-contract update", procedure)

    def test_upgrade_procedure_is_the_latest_first_routing_owner(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        procedure_path = SKILL_ROOT / "references/upgrade.md"
        procedure = procedure_path.read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        architecture = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
        self.assertTrue(procedure_path.is_file())
        self.assertIn("upgrade vault latest", skill.casefold())
        self.assertIn("references/upgrade.md", skill)
        self.assertIn("upgrade vault latest", procedure.casefold())
        self.assertIn("migrate vault latest", procedure.casefold())
        self.assertIn("deep review vault", procedure.casefold())
        self.assertIn("deep update vault", procedure.casefold())
        self.assertIn("Your vault is already current. No files changed.", procedure)
        self.assertIn("re-orient", procedure.casefold())
        self.assertIn("existing deep-maintenance", procedure.casefold())
        self.assertIn("upgrade vault latest", readme.casefold())
        self.assertIn("latest-first upgrade orchestration", architecture.casefold())
        self.assertIn("`latest` is derived", architecture.casefold())

    def test_migration_eval_corpus_covers_natural_language_boundaries(self) -> None:
        evals = json.loads(
            (SKILL_ROOT / "evals/evals.json").read_text(encoding="utf-8")
        )["evals"]
        prompts = {str(case["prompt"]) for case in evals}
        required = {
            "Migrate my SelfContext vault to the latest supported schema.",
            "Upgrade this vault to the latest supported schema.",
            "Check whether my vault needs migration.",
            "Show me a migration plan for my old SelfContext vault, but do not change anything.",
            "Deep review my old vault.",
            "Deep lint my vault.",
            "Deep update my old vault.",
            "Update my Writing vertical contract using only its documented migration.",
            "migrate vault latest",
            "deep review vault",
            "deep update vault",
            "migrate self-context latest",
        }
        self.assertTrue(required.issubset(prompts))

    def test_vertical_procedures_document_historical_upgrade_guidance(self) -> None:
        for record in self.records:
            procedure = (
                SKILL_ROOT / str(record["procedure_path"])
            ).read_text(encoding="utf-8").casefold()
            self.assertIn("historical-upgrade", procedure, str(record["id"]))
            self.assertIn("upgrade", procedure, str(record["id"]))
            self.assertIn("ambiguous", procedure, str(record["id"]))

    def test_upgrade_eval_corpus_covers_latest_first_boundaries(self) -> None:
        evals = json.loads(
            (SKILL_ROOT / "evals/evals.json").read_text(encoding="utf-8")
        )["evals"]
        prompts = {str(case["prompt"]) for case in evals}
        required = {
            "upgrade vault latest",
            "Bring my vault fully up to date with the current SelfContext model.",
            "Make my vault current with this version of SelfContext.",
            "My vault is already current; check whether anything needs changing.",
            "Upgrade a synthetic current-schema vault with clearly relevant historical project lifecycle evidence that belongs in the newly available Ventures / Projects area.",
            "Upgrade a synthetic current-schema vault with no evidence for a newly available vertical.",
            "Upgrade a synthetic vault where a possible historical ownership move is genuinely ambiguous, but unrelated schema and index updates are safe.",
            "Upgrade a synthetic vault whose SCHEMA.md is malformed or declares a future unsupported schema.",
            "Upgrade a synthetic schema 0.2 vault containing a vertical contract version newer than the repository supports.",
        }
        self.assertTrue(required.issubset(prompts))

    def test_latest_first_runtime_policy_is_documented_without_a_second_version_axis(self) -> None:
        architecture = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
        schema = (SKILL_ROOT / "references/vault-schema.md").read_text(encoding="utf-8")
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        adr = (ROOT / "docs/decisions/0020-latest-first-runtime-compatibility.md").read_text(encoding="utf-8")
        combined = "\n".join((architecture, schema, skill, adr)).casefold()
        self.assertIn("latest-first", combined)
        self.assertIn("upgrade vault latest", combined)
        self.assertIn("migration source", combined)
        self.assertIn("safe compatibility blocker", combined)
        self.assertIn("future", combined)
        self.assertIn("combinatorial", combined)
        self.assertIn("no global", combined)
        self.assertIn("silently", combined)
        self.assertIn("--migration-source", (SKILL_ROOT / "references/review-and-lint.md").read_text(encoding="utf-8"))

    def test_latest_first_lint_docs_separate_runtime_and_source_inspection(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        architecture = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
        review_and_lint = (SKILL_ROOT / "references/review-and-lint.md").read_text(encoding="utf-8")
        combined = "\n".join((skill, architecture, review_and_lint)).casefold()
        self.assertIn("### current-runtime validation", review_and_lint.casefold())
        self.assertIn("### migration-source inspection", review_and_lint.casefold())
        self.assertIn("upgrade vault latest", combined)
        self.assertIn("migration source", combined)
        self.assertNotIn("schema 0.1 first meaningful mutation", combined)
        self.assertNotIn("ordinary lint is the fast backward-compatible path", combined)

    def test_consistency_test_is_independent_of_a_real_vault(self) -> None:
        # This test does not open vault/; the actual ignored vault, when
        # present, is intentionally outside the consistency contract.
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertTrue(any(line.strip() == "/vault/" for line in gitignore.splitlines()))


if __name__ == "__main__":
    unittest.main()
