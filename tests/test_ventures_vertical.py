from __future__ import annotations

import datetime as date
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lint_vault  # type: ignore  # noqa: E402
import migrate_vault  # type: ignore  # noqa: E402
import search_vault  # type: ignore  # noqa: E402
import sync_indexes  # type: ignore  # noqa: E402
import vault_utils  # type: ignore  # noqa: E402


CATALOG_START = "<!-- selfcontext:catalog:start -->"
CATALOG_END = "<!-- selfcontext:catalog:end -->"


class VenturesVerticalTests(unittest.TestCase):
    def make_vault(
        self,
        root: Path,
        *,
        schema: str = "0.2",
        contracts: tuple[str, ...] = (),
        areas: tuple[str, ...] = (),
        root_links: tuple[str, ...] | None = None,
    ) -> Path:
        """Create a fictional vault without touching the repository vault."""

        vault = root / "vault"
        for directory in ("core", "review", "sources", "derived", *areas):
            (vault / directory).mkdir(parents=True, exist_ok=True)

        requested_schema_text = f"# Synthetic Schema\n\nschema_version: {schema}\n"
        if schema == "0.2":
            requested_schema_text += "vertical_contracts:\n"
            requested_schema_text += "".join(f"  - {entry}\n" for entry in contracts)

        # Fixture setup must use current control metadata because catalog
        # writes are now runtime-gated.  Restore the requested historical or
        # stale contract state after setup so those cases remain migration and
        # diagnosis fixtures rather than legacy runtime writes.
        setup_contracts = tuple(
            f"{entry.split('@', 1)[0]}@1" for entry in contracts
        )
        setup_schema_text = "# Synthetic Schema\n\nschema_version: 0.2\nvertical_contracts:\n"
        setup_schema_text += "".join(f"  - {entry}\n" for entry in setup_contracts)
        (vault / "SCHEMA.md").write_text(setup_schema_text, encoding="utf-8")

        if root_links is None:
            root_links = areas
        links = [
            "- [Schema](SCHEMA.md)",
            "- [Operation log](log.md)",
            "- [Core](core/index.md)",
            "- [Review](review/index.md)",
            "- [Sources](sources/index.md)",
            "- [Derived](derived/index.md)",
        ]
        links.extend(
            f"- [{area.title()} context]({area}/index.md)" for area in root_links
        )
        (vault / "index.md").write_text(
            "# Synthetic Vault\n\n" + "\n".join(links) + "\n\n",
            encoding="utf-8",
        )
        (vault / "log.md").write_text("# Synthetic Operation Log\n", encoding="utf-8")
        for directory in ("core", "review", "sources", "derived", *areas):
            (vault / directory / "index.md").write_text(
                f"# {directory.title()} Context\n\n",
                encoding="utf-8",
            )

        synchronized = sync_indexes.synchronize(vault, write=True)
        self.assertFalse(
            any(item.get("severity") == "error" for item in synchronized["findings"]),
            synchronized,
        )
        (vault / "SCHEMA.md").write_text(requested_schema_text, encoding="utf-8")
        return vault

    @staticmethod
    def write_page(
        vault: Path,
        relative: str = "ventures/harbor-prototype.md",
        *,
        title: str = "Harbor Prototype",
        status: str = "active",
        assertion_kind: str = "user_stated_fact",
        stale_after: str = "null",
    ) -> Path:
        path = vault / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"""---
type: concept
title: {title}
description: Fictional initiative record for a Ventures integration test.
tags:
  - synthetic
  - ventures
status: {status}
generated: 2026-08-14
verified: null
sources: []
assertion_kind: {assertion_kind}
stale_after: {stale_after}
---

## Purpose

A fictional prototype used to test initiative continuity.

## Initiative lifecycle

active

## Current state

A fictional milestone is recorded without a claim about market success.
""",
            encoding="utf-8",
        )
        return path

    @staticmethod
    def snapshot(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    @staticmethod
    def deep_report(vault: Path) -> dict[str, object]:
        return lint_vault.deep_lint_vault(vault, date.date(2026, 8, 14))

    def test_catalog_procedure_and_advisor_metadata_are_consistent(self) -> None:
        catalog = vault_utils.load_vertical_catalog()
        record = next(
            item for item in vault_utils.catalog_records(catalog) if item["id"] == "ventures"
        )
        self.assertEqual(
            {
                "display_name": record["display_name"],
                "contract_version": record["contract_version"],
                "vault_area": record["vault_area"],
                "index_path": record["index_path"],
                "procedure_path": record["procedure_path"],
                "advisor_pack": record["advisor_pack"],
            },
            {
                "display_name": "Ventures / Projects",
                "contract_version": 1,
                "vault_area": "ventures",
                "index_path": "ventures/index.md",
                "procedure_path": "references/ventures.md",
                "advisor_pack": "ventures-advisor",
            },
        )
        self.assertEqual(vault_utils.validate_vertical_catalog(), [])

        procedure = ROOT / ".agents/skills/self-context/references/ventures.md"
        header = vault_utils.procedure_header(procedure)
        self.assertEqual(header["vertical_id"], "ventures")
        self.assertEqual(header["contract_version"], 1)
        self.assertEqual(header["vault_area"], "ventures")
        self.assertEqual(header["advisor_skill"], "ventures-advisor")
        procedure_text = procedure.read_text(encoding="utf-8")
        self.assertIn("## Contract migrations", procedure_text)
        for phrase in (
            "initiative lifecycle",
            "stale claim needs freshness confirmation",
            "proposal is not a commitment",
            "Career contract `career@1` remains semantically valid",
            "Read-only work never creates or",
        ):
            self.assertIn(phrase, procedure_text)

        skill_dir = ROOT / ".agents/skills/ventures-advisor"
        metadata = json.loads((skill_dir / "evals/evals.json").read_text(encoding="utf-8"))
        triggers = json.loads(
            (skill_dir / "evals/trigger-evals.json").read_text(encoding="utf-8")
        )
        self.assertEqual(metadata["skill_name"], "ventures-advisor")
        self.assertGreaterEqual(len(metadata["evals"]), 16)
        self.assertGreaterEqual(len(triggers), 20)
        self.assertTrue((skill_dir / "SKILL.md").read_text(encoding="utf-8").startswith("---\n"))

    def test_schema_02_selectively_enables_exact_ventures_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(
                Path(temporary),
                contracts=("ventures@1",),
                areas=("ventures",),
                root_links=("ventures",),
            )
            self.write_page(vault)
            sync_indexes.synchronize(vault, write=True)
            report = self.deep_report(vault)

            errors = [item for item in report["findings"] if item["severity"] == "error"]
            self.assertEqual(errors, [])
            self.assertEqual(report["enabled_verticals"], ["ventures"])
            self.assertEqual(report["applied_vertical_contracts"], ["ventures@1"])
            self.assertIn("ventures@1", report["available_vertical_contracts"])
            self.assertFalse((vault / "career").exists())
            self.assertFalse((vault / "learning").exists())

    def test_schema_02_area_marker_mismatches_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            area_without_marker = self.make_vault(
                root / "area-without-marker",
                areas=("ventures",),
                root_links=("ventures",),
            )
            report = self.deep_report(area_without_marker)
            self.assertTrue(
                any(
                    item["severity"] == "error"
                    and "present but not versioned" in item["message"]
                    for item in report["findings"]
                )
            )

            marker_without_area = self.make_vault(
                root / "marker-without-area",
                contracts=("ventures@1",),
            )
            report = self.deep_report(marker_without_area)
            self.assertTrue(
                any(
                    item["severity"] == "error"
                    and "missing its area" in item["message"]
                    for item in report["findings"]
                )
            )

    def test_schema_02_contract_version_currency_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            older = self.make_vault(
                root / "older",
                contracts=("ventures@0",),
                areas=("ventures",),
                root_links=("ventures",),
            )
            older_report = self.deep_report(older)
            older_findings = older_report["findings"]
            self.assertTrue(
                any(item["classification"] == "vertical-contract-update" for item in older_findings)
            )
            self.assertEqual(
                older_report["runtime_compatibility"]["state"],
                "older-contract",
            )
            ordinary_errors, _ = lint_vault.lint_vault(older, date.date(2026, 8, 14))
            self.assertTrue(
                any("Older SelfContext vertical contract detected" in error for error in ordinary_errors)
            )
            source_report = lint_vault.deep_lint_vault(
                older,
                date.date(2026, 8, 14),
                allow_legacy_source=True,
            )
            self.assertFalse(
                any(
                    item["severity"] == "error"
                    and item["classification"] == "runtime-contract"
                    for item in source_report["findings"]
                )
            )

            future = self.make_vault(
                root / "future",
                contracts=("ventures@2",),
                areas=("ventures",),
                root_links=("ventures",),
            )
            future_findings = self.deep_report(future)["findings"]
            self.assertTrue(
                any(
                    item["severity"] == "error"
                    and "newer than available" in item["message"]
                    for item in future_findings
                )
            )

    def test_read_only_absent_ventures_stays_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            vault = self.make_vault(project)
            before = self.snapshot(project)

            search = search_vault.search_vault(vault, "active projects", vertical="ventures")
            self.assertEqual(search["results"], [])
            lint_vault.deep_lint_vault(vault, date.date(2026, 8, 14))
            sync_indexes.synchronize(vault, write=False)

            self.assertEqual(before, self.snapshot(project))
            self.assertFalse((vault / "ventures").exists())
            self.assertNotIn("ventures@1", (vault / "SCHEMA.md").read_text(encoding="utf-8"))
            self.assertFalse((project / "backups").exists())

    def test_schema_01_legacy_ventures_is_inferred_without_contract_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(
                Path(temporary),
                schema="0.1",
                areas=("ventures",),
                root_links=("ventures",),
            )
            report = self.deep_report(vault)
            self.assertEqual(report["enabled_verticals"], [])
            self.assertEqual(report["legacy_inferred_verticals"], ["ventures"])
            self.assertEqual(report["applied_vertical_contracts"], [])
            self.assertNotIn("vertical_contracts:", (vault / "SCHEMA.md").read_text())

            before = self.snapshot(vault)
            plan = migrate_vault.plan_migration(vault)
            self.assertIn("ventures", plan["inferred_enabled_verticals"])
            self.assertIn("ventures@1", plan["enabled_vertical_contracts"])
            self.assertEqual(before, self.snapshot(vault))
            self.assertFalse((vault.parent / "backups").exists())

    def test_search_index_and_deep_lint_recognize_ventures_without_special_branches(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.make_vault(
                Path(temporary),
                contracts=("ventures@1",),
                areas=("ventures",),
                root_links=("ventures",),
            )
            self.write_page(vault, title="Harbor Prototype")
            sync_result = sync_indexes.synchronize(vault, write=True)
            self.assertEqual(sync_result["changed"], ["ventures/index.md"])
            self.assertIn("Harbor Prototype", (vault / "ventures/index.md").read_text())
            self.assertIn(CATALOG_START, (vault / "ventures/index.md").read_text())
            self.assertIn(CATALOG_END, (vault / "ventures/index.md").read_text())

            result = search_vault.search_vault(vault, "Harbor Prototype", vertical="ventures")
            self.assertEqual(result["results"][0]["path"], "ventures/harbor-prototype.md")
            self.assertEqual(result["results"][0]["vertical"], "ventures")
            self.assertEqual(
                search_vault.search_vault(vault, "Harbor Prototype", vertical="career")["results"],
                [],
            )

            report = self.deep_report(vault)
            page = next(item for item in report["pages"] if item["path"] == "ventures/harbor-prototype.md")
            self.assertEqual(page["vertical"], "ventures")
            self.assertEqual(page["owner_index"], "ventures/index.md")
            self.assertFalse(any(item["severity"] == "error" for item in report["findings"]))


if __name__ == "__main__":
    unittest.main()
