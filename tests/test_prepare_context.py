from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/self-context/scripts"
TESTS = ROOT / "tests"
for import_path in (SCRIPTS, TESTS):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

import prepare_context  # type: ignore  # noqa: E402
import search_vault  # type: ignore  # noqa: E402
from synthetic_vault import (  # type: ignore  # noqa: E402
    SENSITIVE_BODY_MARKER,
    build_synthetic_vault,
    tree_snapshot,
    write_page,
)


class PrepareContextTests(unittest.TestCase):
    @staticmethod
    def append_log_entries(vault: Path, count: int) -> None:
        log = vault / "log.md"
        text = log.read_text(encoding="utf-8")
        entries = "".join(
            f"\n## 2026-08-{number:02d} - synthetic-{number}\n\n"
            f"- operation: synthetic-{number}\n"
            f"- summary: bounded continuity entry {number}.\n"
            for number in range(1, count + 1)
        )
        log.write_text(text + entries, encoding="utf-8")

    def test_cli_returns_the_same_compact_json_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "prepare_context.py"),
                    str(vault),
                    "--scope",
                    "career",
                    "--anchor",
                    "Harbor Launch",
                    "--recent-limit",
                    "1",
                    "--result-limit",
                    "1",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            packet = json.loads(result.stdout)
            self.assertEqual(packet["runtime"]["state"], "current")
            self.assertEqual(packet["controls"]["scope"], ["career"])
            self.assertLessEqual(len(packet["matches"]), 1)

    def test_current_packet_is_bounded_scoped_and_compact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            self.append_log_entries(vault, 5)
            write_page(
                vault,
                "career/bounded-evidence.md",
                title="Bounded Evidence",
                description="metadata prefix " + ("x" * 1200) + " METADATA_BODY_MARKER",
                body=("bounded body prefix\n" + ("y" * 1200) + "\n" + SENSITIVE_BODY_MARKER + "\n"),
            )
            before = tree_snapshot(vault)

            packet = prepare_context.prepare_context(
                vault,
                explicit_scope=["./career/"],
                anchors=["Harbor Launch", "harbor delivery"],
                recent_limit=2,
                result_limit=2,
                expand_linked_sources=True,
            )

            self.assertEqual(packet["runtime"]["state"], "current")
            self.assertEqual(packet["controls"]["scope"], ["career"])
            self.assertTrue(packet["controls"]["search_performed"])
            self.assertEqual(len(packet["recent"]), 2)
            self.assertEqual(
                {item["operation"] for item in packet["recent"]},
                {"synthetic-4", "synthetic-5"},
            )
            self.assertLessEqual(len(packet["matches"]), 2)
            self.assertLessEqual(len(packet["linked_sources"]), 3)
            self.assertEqual(packet["matches"][0]["path"], "career/harbor-launch.md")
            self.assertIn("harbor delivery", packet["matches"][0]["aliases"])
            self.assertEqual(
                packet["matches"][0]["matched_anchors"],
                ["Harbor Launch", "harbor delivery"],
            )
            self.assertEqual(
                {item["path"] for item in packet["navigation"]},
                {"index.md", "career/index.md"},
            )
            self.assertNotIn("learning/index.md", {item["path"] for item in packet["navigation"]})
            serialized = json.dumps(packet, sort_keys=True)
            self.assertNotIn(SENSITIVE_BODY_MARKER, serialized)

            bounded = prepare_context.prepare_context(
                vault,
                scope=["career"],
                anchors=["Bounded Evidence"],
                result_limit=1,
            )
            bounded_serialized = json.dumps(bounded, sort_keys=True)
            self.assertNotIn(SENSITIVE_BODY_MARKER, bounded_serialized)
            self.assertNotIn("METADATA_BODY_MARKER", bounded_serialized)
            self.assertEqual(before, tree_snapshot(vault))

    def test_old_future_and_malformed_vaults_report_blockers_without_search_or_writes(self) -> None:
        variants = ("0.1", "future", "malformed")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for variant in variants:
                project = root / variant
                vault = build_synthetic_vault(
                    project, schema_version="0.1" if variant == "0.1" else "0.2"
                )
                if variant == "future":
                    (vault / "SCHEMA.md").write_text(
                        "# Synthetic Schema\n\nschema_version: 0.3\n",
                        encoding="utf-8",
                    )
                elif variant == "malformed":
                    (vault / "SCHEMA.md").write_text(
                        "# Synthetic Schema\n\nschema_version: not-a-version\n",
                        encoding="utf-8",
                    )
                before = tree_snapshot(vault)

                packet = prepare_context.prepare_context(
                    vault,
                    scope=["career"],
                    query="Harbor Launch",
                    recent_limit=1,
                )

                self.assertFalse(packet["runtime"]["ok"], variant)
                self.assertEqual(packet["matches"], [], variant)
                self.assertEqual(packet["linked_sources"], [], variant)
                self.assertEqual(packet["controls"]["search_performed"], False)
                self.assertTrue(
                    any(item["classification"] == "search" for item in packet["findings"]),
                    variant,
                )
                self.assertEqual(before, tree_snapshot(vault), variant)

    def test_missing_and_empty_vaults_are_reported_without_initialization(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missing = root / "missing-vault"
            packet = prepare_context.prepare_context(
                missing, scope=["career"], query="anything"
            )
            self.assertEqual(packet["runtime"]["state"], "missing")
            self.assertEqual(packet["matches"], [])
            self.assertFalse(missing.exists())

            empty = root / "empty-vault"
            empty.mkdir()
            before = tree_snapshot(empty)
            packet = prepare_context.prepare_context(
                empty, scope=["career"], query="anything"
            )
            self.assertEqual(packet["runtime"]["state"], "empty")
            self.assertEqual(packet["matches"], [])
            self.assertEqual(before, tree_snapshot(empty))

            incompatible = root / "not-a-vault"
            incompatible.write_text("not a vault", encoding="utf-8")
            packet = prepare_context.prepare_context(
                incompatible, scope=["career"], query="anything"
            )
            self.assertNotEqual(packet["runtime"]["state"], "current")
            self.assertEqual(packet["matches"], [])
            self.assertEqual(incompatible.read_text(encoding="utf-8"), "not a vault")

    def test_explicit_scope_and_manual_navigation_do_not_activate_absent_verticals(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            before = tree_snapshot(vault)

            packet = prepare_context.prepare_context(
                vault,
                scope=["career"],
                query="Fictional",
                navigation_paths=["learning/index.md", "media/index.md"],
            )

            self.assertEqual(packet["controls"]["requested_scope"], ["career"])
            self.assertEqual(packet["controls"]["scope"], ["career"])
            self.assertTrue(packet["matches"])
            self.assertTrue(all(item["path"].startswith("career/") for item in packet["matches"]))
            navigation = {item["path"] for item in packet["navigation"]}
            self.assertIn("learning/index.md", navigation)
            self.assertNotIn("media/index.md", navigation)
            self.assertFalse((vault / "media").exists())
            self.assertEqual(before, tree_snapshot(vault))

    def test_multiple_anchors_use_existing_exact_id_title_and_alias_search_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            write_page(
                vault,
                "core/stable-record.md",
                title="Stable Record",
                aliases=("Stable Alias",),
                extra_fields={"id": "stable-record-42"},
                body="A fictional stable record for exact lookup tests.\n",
            )

            by_id = prepare_context.prepare_context(
                vault, scope=["core"], anchors=["stable-record-42"], result_limit=3
            )
            by_alias = prepare_context.prepare_context(
                vault, scope=["core"], anchors=["Stable Alias"], result_limit=3
            )

            self.assertEqual(by_id["matches"][0]["match_type"], "exact_id")
            self.assertEqual(by_id["matches"][0]["path"], "core/stable-record.md")
            self.assertEqual(by_alias["matches"][0]["match_type"], "exact_alias")
            self.assertEqual(by_alias["matches"][0]["path"], "core/stable-record.md")
            self.assertEqual(by_alias["matches"][0]["id"], "stable-record-42")

    def test_multi_anchor_search_reuses_one_corpus_and_preserves_merged_results(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            anchors = ["Harbor Launch", "harbor delivery", "launch example"]
            search_limit = 7
            reports = [
                (
                    number,
                    anchor,
                    search_vault.search_vault(
                        vault,
                        anchor,
                        limit=search_limit,
                        scope=["career"],
                        expand_linked_sources=True,
                        include_identity=True,
                    ),
                )
                for number, anchor in enumerate(anchors)
            ]
            expected_matches, expected_linked = prepare_context._merge_search_results(
                reports,
                result_limit=4,
                linked_source_limit=2,
            )

            with mock.patch.object(
                search_vault,
                "durable_page_records",
                wraps=search_vault.durable_page_records,
            ) as load_records, mock.patch.object(
                search_vault,
                "_index_record",
                wraps=search_vault._index_record,
            ) as index_record:
                packet = prepare_context.prepare_context(
                    vault,
                    scope=["career"],
                    anchors=anchors,
                    result_limit=4,
                    linked_source_limit=2,
                    expand_linked_sources=True,
                )

            self.assertEqual(load_records.call_count, 1)
            indexed_paths = [
                str(call.args[0]["path"]) for call in index_record.call_args_list
            ]
            self.assertCountEqual(
                indexed_paths,
                [
                    "career/harbor-launch.md",
                    "career/archived-role.md",
                    "career/superseded-launch.md",
                ],
            )
            self.assertNotIn("core/decision-trail.md", indexed_paths)
            self.assertNotIn("sources/harbor-notes.md", indexed_paths)
            self.assertIn(
                "sources/harbor-notes.md",
                [item["path"] for item in packet["linked_sources"]],
            )
            self.assertEqual(packet["matches"], expected_matches)
            self.assertEqual(packet["linked_sources"], expected_linked)

    def test_separate_preparations_rebuild_current_filesystem_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            first = prepare_context.prepare_context(
                vault,
                scope=["career"],
                anchors=["Harbor Launch"],
                result_limit=1,
            )
            self.assertEqual(first["matches"][0]["path"], "career/harbor-launch.md")

            write_page(
                vault,
                "career/harbor-launch.md",
                title="Fresh Launch Anchor",
                description="A newly written fictional retrieval fixture.",
                body="Fresh launch anchor content.\n",
            )
            second = prepare_context.prepare_context(
                vault,
                scope=["career"],
                anchors=["Fresh Launch Anchor"],
                result_limit=1,
            )

            self.assertEqual(second["matches"][0]["path"], "career/harbor-launch.md")
            self.assertEqual(second["matches"][0]["title"], "Fresh Launch Anchor")

    def test_result_and_linked_source_caps_are_applied_after_composition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            for number in range(1, 6):
                source = f"../sources/preparation-source-{number}.md"
                write_page(
                    vault,
                    f"sources/preparation-source-{number}.md",
                    page_type="source",
                    title=f"Preparation Source {number}",
                    assertion_kind="source_record",
                    body=f"Fictional source {number}.\n",
                )
                write_page(
                    vault,
                    f"career/preparation-evidence-{number}.md",
                    title=f"Preparation Evidence {number}",
                    sources=(source,),
                    body=f"Fictional preparation evidence {number}.\n",
                )

            packet = prepare_context.prepare_context(
                vault,
                scope=["career"],
                anchors=["Preparation Evidence"],
                result_limit=2,
                linked_source_limit=2,
                expand_linked_sources=True,
            )

            self.assertLessEqual(len(packet["matches"]), 2)
            self.assertLessEqual(len(packet["linked_sources"]), 2)
            self.assertTrue(all(item.get("linked_from") for item in packet["linked_sources"]))

    def test_unscoped_search_is_not_implicitly_global(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            packet = prepare_context.prepare_context(vault, anchors=["Harbor Launch"])
            self.assertEqual(packet["matches"], [])
            self.assertFalse(packet["controls"]["search_performed"])
            self.assertTrue(
                any(item.get("state") == "scope-required" for item in packet["findings"])
            )


if __name__ == "__main__":
    unittest.main()
