import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
LINT = SCRIPTS / "lint_vault.py"


def page(page_type: str = "concept", assertion: str = "user_stated_fact", title: str = "Synthetic Page", extra: str = "") -> str:
    return f"""---
type: {page_type}
title: {title}
description: Synthetic page for deep-lint tests.
tags:
  - synthetic
status: active
generated: 2026-08-12
verified: null
sources: []
assertion_kind: {assertion}
stale_after: null
{extra}---

Synthetic page body.
"""


class DeepLintTests(unittest.TestCase):
    def base_vault(self, root: Path, *, schema: str = "0.1") -> Path:
        vault = root / "vault"
        for directory in ("core", "review", "sources", "derived"):
            (vault / directory).mkdir(parents=True)
        (vault / "SCHEMA.md").write_text(f"# Schema\n\nschema_version: {schema}\n", encoding="utf-8")
        (vault / "index.md").write_text(
            "# Root\n\nSCHEMA.md\nlog.md\n"
            "- [Core](core/index.md)\n- [Review](review/index.md)\n"
            "- [Sources](sources/index.md)\n- [Derived](derived/index.md)\n",
            encoding="utf-8",
        )
        (vault / "log.md").write_text("# Log\n", encoding="utf-8")
        for directory in ("core", "review", "sources", "derived"):
            (vault / directory / "index.md").write_text(f"# {directory}\n", encoding="utf-8")
        return vault

    def run_deep_lint(self, vault: Path, *args: str) -> tuple[subprocess.CompletedProcess, dict]:
        result = subprocess.run(
            [sys.executable, str(LINT), "--deep", "--format", "json", *args, str(vault)],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        return result, json.loads(result.stdout)

    def write_index(self, vault: Path, relative: str, links: list[str]) -> None:
        path = vault / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Synthetic index\n\n" + "\n".join(links) + "\n", encoding="utf-8")

    def reachability_paths(self, report: dict) -> set[str]:
        return {
            str(item["path"])
            for item in report["findings"]
            if item["classification"] == "root-reachability"
        }

    def test_root_reachability_and_nearest_index_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "core" / "orphan.md").write_text(page(title="Orphan"), encoding="utf-8")
            _, report = self.run_deep_lint(vault)
            classes = {item["classification"] for item in report["findings"]}
            self.assertIn("root-reachability", classes)
            self.assertIn("catalog-sync", classes)

    def test_managed_catalog_sync_and_dead_entries_are_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            index = vault / "core" / "index.md"
            index.write_text(
                "# core\n\n<!-- selfcontext:catalog:start -->\n"
                "- [Dead](missing.md) — dead `active`\n"
                "<!-- selfcontext:catalog:end -->\n",
                encoding="utf-8",
            )
            _, report = self.run_deep_lint(vault)
            classes = [item["classification"] for item in report["findings"]]
            self.assertIn("catalog-sync", classes)
            self.assertIn("dead-catalog-entry", classes)

    def test_managed_owner_missing_page_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "core" / "orphan.md").write_text(page(title="Orphan"), encoding="utf-8")
            (vault / "core" / "index.md").write_text(
                "# core\n\n<!-- selfcontext:catalog:start -->\n"
                "<!-- selfcontext:catalog:end -->\n",
                encoding="utf-8",
            )
            _, report = self.run_deep_lint(vault)
            self.assertTrue(any(item["classification"] == "nearest-index-ownership" for item in report["findings"]))

    def test_index_only_page_is_warning_when_catalog_is_synchronized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            page_path = vault / "core" / "orphan.md"
            page_path.write_text(page(title="Index Only"), encoding="utf-8")
            import sys as _sys
            _sys.path.insert(0, str(SCRIPTS))
            import sync_indexes
            sync_indexes.synchronize(vault, write=True)
            _, report = self.run_deep_lint(vault)
            weak = [item for item in report["findings"] if item["classification"] == "weak-connectivity"]
            self.assertEqual(len(weak), 1)
            self.assertEqual(weak[0]["severity"], "warning")

    def test_title_alias_collision_and_supersession_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "core" / "one.md").write_text(page(title="Same Name", extra="aliases:\n  - Shared\n"), encoding="utf-8")
            (vault / "core" / "two.md").write_text(page(title="Other", extra="aliases:\n  - same name\n"), encoding="utf-8")
            (vault / "core" / "old.md").write_text(page(title="Old", extra="status: superseded\n"), encoding="utf-8")
            _, report = self.run_deep_lint(vault)
            self.assertTrue(any(item["classification"] == "title-alias-collision" for item in report["findings"]))
            self.assertTrue(any(item["classification"] == "supersession" for item in report["findings"]))

    def test_type_assertion_and_path_compatibility(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "sources" / "wrong.md").write_text(page(assertion="user_stated_fact", title="Wrong Source"), encoding="utf-8")
            (vault / "derived" / "wrong.md").write_text(page(page_type="concept", assertion="derived_synthesis", title="Wrong Derived"), encoding="utf-8")
            _, report = self.run_deep_lint(vault)
            classes = [item["classification"] for item in report["findings"]]
            self.assertIn("type-assertion-compatibility", classes)
            self.assertIn("path-compatibility", classes)

    def test_derived_source_chain_and_newer_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "derived" / "base.md").write_text(page(page_type="synthesis", assertion="derived_synthesis", title="Base", extra="sources:\n  - ../core/fact.md\n"), encoding="utf-8")
            (vault / "derived" / "top.md").write_text(page(page_type="synthesis", assertion="derived_synthesis", title="Top", extra="generated: 2026-01-01\nsources:\n  - base.md\n"), encoding="utf-8")
            (vault / "core" / "fact.md").write_text(page(title="Fact", extra="generated: 2026-08-12\n"), encoding="utf-8")
            import sys as _sys
            _sys.path.insert(0, str(SCRIPTS))
            import sync_indexes
            sync_indexes.synchronize(vault, write=True)
            _, report = self.run_deep_lint(vault)
            classes = [item["classification"] for item in report["findings"]]
            self.assertIn("derived-source-chain", classes)
            self.assertIn("derived-freshness", classes)

    def test_json_inventory_includes_compact_metadata_links_and_source_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "career").mkdir()
            (vault / "career" / "index.md").write_text("# Career\n", encoding="utf-8")
            (vault / "career" / "role.md").write_text(
                page(title="Synthetic Career Role", extra="id: career-role\n"),
                encoding="utf-8",
            )
            with (vault / "index.md").open("a", encoding="utf-8") as root_index:
                root_index.write("- [Career](career/index.md)\n")
            source = vault / "sources" / "evidence.md"
            source.write_text(
                page(
                    page_type="source",
                    assertion="source_record",
                    title="Synthetic Evidence",
                    extra="id: source-evidence\n",
                )
                + "\nLONG_SYNTHETIC_SOURCE_CONTENT_MUST_NOT_APPEAR_IN_INVENTORY\n",
                encoding="utf-8",
            )
            related = vault / "core" / "related.md"
            related.write_text(
                page(title="Related Synthetic Page")
                + "\n[Concept](concept.md)\n",
                encoding="utf-8",
            )
            concept = vault / "core" / "concept.md"
            concept.write_text(
                page(
                    title="Synthetic Concept",
                    extra=(
                        "id: concept-stable-id\n"
                        "aliases:\n"
                        "  - Compact Concept\n"
                        "tags:\n"
                        "  - synthetic\n"
                        "  - triage\n"
                        "sources:\n"
                        "  - ../sources/evidence.md\n"
                        "  - https://example.test/synthetic-source\n"
                    ),
                )
                + "\n[Related](related.md)\n[Broken](missing.md)\nBODY_ONLY_SYNTHETIC_SECRET_7f3b1\n",
                encoding="utf-8",
            )

            sys.path.insert(0, str(SCRIPTS))
            import sync_indexes
            sync_indexes.synchronize(vault, write=True)

            first = self.run_deep_lint(vault)
            second = self.run_deep_lint(vault)
            self.assertEqual(first[0].returncode, second[0].returncode)
            self.assertEqual(first[0].stdout, second[0].stdout)
            report = first[1]
            pages = report["pages"]
            self.assertEqual([item["path"] for item in pages], sorted(item["path"] for item in pages))
            item = next(page_item for page_item in pages if page_item["path"] == "core/concept.md")

            self.assertEqual(item["id"], "concept-stable-id")
            self.assertEqual(item["title"], "Synthetic Concept")
            self.assertEqual(item["aliases"], ["Compact Concept"])
            self.assertEqual(item["tags"], ["synthetic", "triage"])
            self.assertEqual(item["type"], "concept")
            self.assertEqual(item["assertion_kind"], "user_stated_fact")
            self.assertEqual(item["status"], "active")
            self.assertEqual(item["generated"], "2026-08-12")
            self.assertIsNone(item["verified"])
            self.assertIsNone(item["stale_after"])
            self.assertEqual(item["owner_index"], "core/index.md")
            self.assertIsNone(item["vertical"])
            career_item = next(page_item for page_item in pages if page_item["path"] == "career/role.md")
            self.assertEqual(career_item["vertical"], "career")
            self.assertEqual(career_item["owner_index"], "career/index.md")
            self.assertTrue(item["content_hash"])
            self.assertEqual(item["outbound_links"], ["core/missing.md", "core/related.md"])
            self.assertIn("core/index.md", item["inbound_links"])
            self.assertIn("core/related.md", item["inbound_links"])
            self.assertEqual(item["sources"], ["../sources/evidence.md", "https://example.test/synthetic-source"])

            relationships = item["source_relationships"]
            self.assertEqual(len(relationships), 2)
            internal = next(entry for entry in relationships if entry["internal"])
            self.assertEqual(
                internal,
                {
                    "original": "../sources/evidence.md",
                    "normalized_target": "sources/evidence.md",
                    "internal": True,
                    "external": False,
                    "exists": True,
                    "target_kind": "source",
                },
            )
            external = next(entry for entry in relationships if entry["external"])
            self.assertEqual(external["original"], "https://example.test/synthetic-source")
            self.assertFalse(external["internal"])
            self.assertIsNone(external["exists"])
            self.assertIsNone(external["target_kind"])

            output = first[0].stdout
            self.assertNotIn("BODY_ONLY_SYNTHETIC_SECRET_7f3b1", output)
            self.assertNotIn("LONG_SYNTHETIC_SOURCE_CONTENT_MUST_NOT_APPEAR_IN_INVENTORY", output)
            self.assertNotIn("Synthetic page body", output)
            self.assertNotIn('"body"', output)
            second_item = next(page_item for page_item in second[1]["pages"] if page_item["path"] == "core/concept.md")
            self.assertEqual(item["content_hash"], second_item["content_hash"])

    def test_source_relationships_classify_derived_targets_and_missing_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "sources" / "evidence.md").write_text(
                page(page_type="source", assertion="source_record", title="Evidence"),
                encoding="utf-8",
            )
            (vault / "derived" / "base.md").write_text(
                page(
                    page_type="synthesis",
                    assertion="derived_synthesis",
                    title="Base Synthesis",
                    extra="sources:\n  - ../sources/evidence.md\n",
                ),
                encoding="utf-8",
            )
            (vault / "derived" / "top.md").write_text(
                page(
                    page_type="synthesis",
                    assertion="derived_synthesis",
                    title="Top Synthesis",
                    extra="sources:\n  - base.md\n",
                ),
                encoding="utf-8",
            )
            (vault / "derived" / "missing.md").write_text(
                page(
                    page_type="synthesis",
                    assertion="derived_synthesis",
                    title="Missing Provenance",
                ),
                encoding="utf-8",
            )
            sys.path.insert(0, str(SCRIPTS))
            import sync_indexes
            sync_indexes.synchronize(vault, write=True)
            _, report = self.run_deep_lint(vault)

            top = next(item for item in report["pages"] if item["path"] == "derived/top.md")
            self.assertEqual(top["source_relationships"][0]["normalized_target"], "derived/base.md")
            self.assertEqual(top["source_relationships"][0]["target_kind"], "derived")
            provenance = [
                item for item in report["findings"]
                if item.get("classification") == "provenance" and item.get("path") == "derived/missing.md"
            ]
            self.assertTrue(provenance)
            self.assertIn("has no sources", provenance[0]["message"])

    def test_derived_freshness_is_a_bounded_review_signal_in_text_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "sources" / "newer.md").write_text(
                page(
                    page_type="source",
                    assertion="source_record",
                    title="Newer Source",
                    extra="generated: 2025-01-01\nupdated: 2026-08-12\n",
                ),
                encoding="utf-8",
            )
            (vault / "derived" / "synthesis.md").write_text(
                page(
                    page_type="synthesis",
                    assertion="derived_synthesis",
                    title="Derived Synthesis",
                    extra="generated: 2026-01-01\nsources:\n  - ../sources/newer.md\n",
                ),
                encoding="utf-8",
            )
            sys.path.insert(0, str(SCRIPTS))
            import sync_indexes
            sync_indexes.synchronize(vault, write=True)
            _, report = self.run_deep_lint(vault)
            finding = next(item for item in report["findings"] if item["classification"] == "derived-freshness")
            message = finding["message"]
            self.assertIn("newer generated or updated timestamp", message)
            self.assertIn("Review whether regeneration is needed", message)
            self.assertEqual(finding["source_path"], "sources/newer.md")
            for overclaim in ("materially", "decisive", "wrong", "mandatory"):
                self.assertNotIn(overclaim, message.casefold())

            text_result = subprocess.run(
                [sys.executable, str(LINT), "--deep", "--format", "text", str(vault)],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            self.assertIn(message, text_result.stdout)
            self.assertNotIn("materially updated decisive source", text_result.stdout)

    def test_malformed_metadata_remains_valid_json_and_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "core" / "malformed.md").write_text(
                page(
                    title="Malformed Metadata",
                    extra="tags: synthetic\nsources: ../sources/missing.md\n",
                ),
                encoding="utf-8",
            )
            result, report = self.run_deep_lint(vault)
            self.assertIn(result.returncode, (0, 1))
            self.assertEqual(json.loads(result.stdout), report)
            findings = [
                item for item in report["findings"]
                if item.get("path") == "core/malformed.md"
            ]
            self.assertTrue(any("tags must be a YAML list" in item["message"] for item in findings))
            self.assertTrue(any("sources must be a YAML list" in item["message"] for item in findings))
            page_item = next(item for item in report["pages"] if item["path"] == "core/malformed.md")
            self.assertNotIn("tags", page_item)
            self.assertEqual(page_item["source_relationships"], [])

    def test_root_and_child_indexes_form_a_terminating_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "core" / "index.md").write_text(
                "# Core\n\n- [Root](../index.md)\n", encoding="utf-8"
            )
            first, report = self.run_deep_lint(vault)
            second, repeated = self.run_deep_lint(vault)
            self.assertEqual(first.returncode, second.returncode)
            self.assertEqual(report["snapshot_id"], repeated["snapshot_id"])
            unreachable = self.reachability_paths(report)
            self.assertNotIn("index.md", unreachable)
            self.assertNotIn("core/index.md", unreachable)

    def test_two_index_cycle_and_duplicate_link_terminates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "core" / "index.md").write_text(
                "# Core\n\n- [A](cycle/a/index.md)\n", encoding="utf-8"
            )
            self.write_index(
                vault,
                "core/cycle/a/index.md",
                ["- [B](../b/index.md)", "- [B again](../b/index.md)"],
            )
            self.write_index(vault, "core/cycle/b/index.md", ["- [A](../a/index.md)"])
            _, report = self.run_deep_lint(vault)
            unreachable = self.reachability_paths(report)
            self.assertNotIn("core/cycle/a/index.md", unreachable)
            self.assertNotIn("core/cycle/b/index.md", unreachable)

    def test_self_linked_index_terminates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "core" / "index.md").write_text(
                "# Core\n\n- [Self](index.md)\n- [Self again](index.md)\n", encoding="utf-8"
            )
            _, report = self.run_deep_lint(vault)
            self.assertNotIn("core/index.md", self.reachability_paths(report))

    def test_three_index_cycle_terminates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "core" / "index.md").write_text(
                "# Core\n\n- [A](triangle/a/index.md)\n", encoding="utf-8"
            )
            self.write_index(vault, "core/triangle/a/index.md", ["- [B](../b/index.md)"])
            self.write_index(vault, "core/triangle/b/index.md", ["- [C](../c/index.md)"])
            self.write_index(vault, "core/triangle/c/index.md", ["- [A](../a/index.md)"])
            _, report = self.run_deep_lint(vault)
            unreachable = self.reachability_paths(report)
            self.assertFalse(
                unreachable.intersection(
                    {
                        "core/triangle/a/index.md",
                        "core/triangle/b/index.md",
                        "core/triangle/c/index.md",
                    }
                )
            )

    def test_cyclic_indexes_still_reach_a_durable_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "core" / "index.md").write_text(
                "# Core\n\n- [A](cycle/a/index.md)\n", encoding="utf-8"
            )
            self.write_index(vault, "core/cycle/a/index.md", ["- [B](../b/index.md)"])
            self.write_index(
                vault,
                "core/cycle/b/index.md",
                ["- [A](../a/index.md)", "- [Durable](page.md)"],
            )
            (vault / "core" / "cycle" / "b" / "page.md").write_text(
                page(title="Reachable synthetic page"), encoding="utf-8"
            )
            _, report = self.run_deep_lint(vault)
            self.assertNotIn("core/cycle/b/page.md", self.reachability_paths(report))

    def test_disconnected_cyclic_indexes_remain_unreachable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            self.write_index(vault, "core/disconnected/a/index.md", ["- [B](../b/index.md)"])
            self.write_index(vault, "core/disconnected/b/index.md", ["- [A](../a/index.md)"])
            _, report = self.run_deep_lint(vault)
            unreachable = self.reachability_paths(report)
            self.assertIn("core/disconnected/a/index.md", unreachable)
            self.assertIn("core/disconnected/b/index.md", unreachable)

    def test_snapshot_is_deterministic_for_a_cyclic_index_graph(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            (vault / "core" / "index.md").write_text(
                "# Core\n\n- [A](cycle/a/index.md)\n", encoding="utf-8"
            )
            self.write_index(vault, "core/cycle/a/index.md", ["- [B](../b/index.md)"])
            self.write_index(vault, "core/cycle/b/index.md", ["- [A](../a/index.md)"])
            _, first = self.run_deep_lint(vault)
            _, second = self.run_deep_lint(vault)
            self.assertEqual(first["snapshot_id"], second["snapshot_id"])

    def test_snapshot_ignores_obsidian_and_backup_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = self.base_vault(Path(temporary))
            _, one = self.run_deep_lint(vault)
            (vault / ".obsidian").mkdir()
            (vault / ".obsidian" / "state.json").write_text("viewer", encoding="utf-8")
            root_backup = vault.parent / "backups"
            root_backup.mkdir()
            (root_backup / "vault-20260812T000000Z.zip").write_bytes(b"private")
            _, two = self.run_deep_lint(vault)
            self.assertEqual(one["snapshot_id"], two["snapshot_id"])


if __name__ == "__main__":
    unittest.main()
