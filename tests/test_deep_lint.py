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
