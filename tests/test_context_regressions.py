"""Synthetic regressions for read-time safety and bounded evidence retrieval."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT / "tests", ROOT / ".agents/skills/self-context/scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import ordinary_commit
import prepare_context
import search_vault
import sync_indexes
import vault_utils
from synthetic_vault import backup_paths, build_synthetic_vault, tree_snapshot, write_page


class ContextRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        self.vault = build_synthetic_vault(self.project)

    def prepare(self, **kwargs):
        return prepare_context.prepare_context(
            self.vault, scope=["career"], anchors=["Harbor Launch"], **kwargs
        )

    def test_read_only_queries_do_not_snapshot_and_mutation_packets_do_not_write(self):
        before = tree_snapshot(self.vault)
        with mock.patch.object(vault_utils, "snapshot_id", wraps=vault_utils.snapshot_id) as snapshot:
            self.prepare(include_evidence=True)
            snapshot.assert_not_called()
            packet = self.prepare(for_update=True, include_evidence=True)
            self.assertEqual(snapshot.call_count, 2)
        self.assertTrue(packet["controls"]["mutation_ready"])
        self.assertEqual(packet["controls"]["expected_snapshot"], vault_utils.snapshot_id(self.vault))
        self.assertEqual(tree_snapshot(self.vault), before)
        self.assertEqual(backup_paths(self.project), [])

    def test_mutation_packet_rejects_drift_during_evidence_read(self):
        real_build = search_vault._build_search_corpus

        def change_after_read(*args, **kwargs):
            corpus = real_build(*args, **kwargs)
            page = self.vault / "career/harbor-launch.md"
            page.write_text(page.read_text() + "\nIndependent fictional correction.\n")
            return corpus

        with mock.patch.object(search_vault, "_build_search_corpus", side_effect=change_after_read):
            packet = self.prepare(for_update=True, include_evidence=True)
        self.assertFalse(packet["controls"]["mutation_ready"])
        self.assertIsNone(packet["controls"]["expected_snapshot"])
        self.assertTrue(any(f["classification"] == "mutation-precondition" for f in packet["findings"]))
        self.assertEqual(backup_paths(self.project), [])

    def test_snapshot_failure_never_issues_mutation_precondition(self):
        with mock.patch.object(vault_utils, "snapshot_id", side_effect=OSError("unreadable")):
            packet = self.prepare(for_update=True)
        self.assertFalse(packet["controls"]["mutation_ready"])
        self.assertIsNone(packet["controls"]["expected_snapshot"])

    def test_unreadable_canonical_file_blocks_mutation_snapshots(self):
        read = vault_utils.safe_read_bytes
        before = tree_snapshot(self.vault)

        def unreadable(path):
            if path.name == "harbor-launch.md":
                return None, "OSError: injected unreadable file"
            return read(path)

        with mock.patch.object(vault_utils, "safe_read_bytes", side_effect=unreadable):
            packet = self.prepare(for_update=True)
            result = ordinary_commit.commit_mutation(self.vault, {"writes": {}})
        self.assertFalse(packet["controls"]["mutation_ready"])
        self.assertIsNone(packet["controls"]["expected_snapshot"])
        self.assertEqual(result["state"], "snapshot-error")
        self.assertEqual(tree_snapshot(self.vault), before)
        self.assertEqual(backup_paths(self.project), [])

    def test_missing_preconditions_reject_before_staging(self):
        before = tree_snapshot(self.vault)
        with mock.patch.object(ordinary_commit.shutil, "copytree") as stage:
            for value in (None, "", 123, []):
                with self.subTest(value=value):
                    result = ordinary_commit.commit_mutation(
                        self.vault, {"expected_snapshot": value, "writes": {}}
                    )
                    self.assertEqual(result["state"], "input-invalid")
            result = ordinary_commit.commit_mutation(self.vault, {"writes": {}})
            self.assertEqual(result["state"], "input-invalid")
            stage.assert_not_called()
        self.assertEqual(tree_snapshot(self.vault), before)
        self.assertEqual(backup_paths(self.project), [])

    def test_stale_read_and_stale_create_preserve_independent_changes(self):
        for label in ("career/harbor-launch.md", "career/new-fact.md"):
            with self.subTest(label=label):
                packet = self.prepare(for_update=True)
                target = self.vault / label
                old = target.read_text() if target.exists() else "unused proposed text"
                write_page(self.vault, label, title="Independent fictional update", body="John Doe corrected this.\n")
                before = tree_snapshot(self.vault)
                result = ordinary_commit.commit_mutation(self.vault, {
                    "expected_snapshot": packet["controls"]["expected_snapshot"],
                    "writes": {label: old + "\nStale proposal.\n"},
                })
                self.assertEqual(result["state"], "snapshot-mismatch")
                self.assertEqual(tree_snapshot(self.vault), before)
        self.assertEqual(backup_paths(self.project), [])

    def test_matching_read_time_snapshot_commits(self):
        packet = self.prepare(for_update=True, include_evidence=True)
        label = "career/harbor-launch.md"
        content = (self.vault / label).read_text() + "\nJohn Doe supplied more evidence.\n"
        result = ordinary_commit.commit_mutation(self.vault, {
            "expected_snapshot": packet["controls"]["expected_snapshot"],
            "writes": {label: content},
            "log": {"operation": "ingest", "summary": "Add fictional evidence", "paths": [label]},
        })
        self.assertEqual(result["status"], "success")
        self.assertEqual((self.vault / label).read_text(), content)

    def test_navigation_resolves_only_budgeted_targets_and_reports_truncation(self):
        index = self.vault / "career/index.md"
        text = "# Career\n\n" + "\n".join(f"- [Page {i}](page-{i}.md)" for i in range(200))
        index.write_text(text)
        for limit in (0, 3, 200):
            with self.subTest(limit=limit), mock.patch.object(
                vault_utils, "link_target", wraps=vault_utils.link_target
            ) as resolve:
                record = prepare_context._navigation_record(index, "scope:career", self.vault, limit, [])
                self.assertEqual(resolve.call_count, limit)
                self.assertEqual(len(record["links"]), limit)
                self.assertEqual(record["links_truncated"], limit < 200)
        self.assertEqual(len(vault_utils.markdown_link_records(index, self.vault, text)), 200)

    def test_managed_navigation_parsing_stops_at_limit_plus_lookahead(self):
        # Use the actual renderer to avoid depending on a guessed catalog format.
        text = sync_indexes._format_block(
            sync_indexes._format_entry(f"Page {i}", "Fictional page.", "active", Path(f"page-{i}.md"))
            for i in range(200)
        )
        index = self.vault / "career/index.md"
        index.write_text(text)
        with mock.patch.object(sync_indexes, "_parse_entry_line", wraps=sync_indexes._parse_entry_line) as parse:
            record = prepare_context._navigation_record(index, "scope:career", self.vault, 3, [])
        self.assertEqual(parse.call_count, 4)
        self.assertEqual(len(record["managed_entries"]), 3)
        self.assertTrue(record["managed_entries_truncated"])
        self.assertEqual(len(sync_indexes.managed_entries(text)), 200)

    def test_coverage_order_is_shared_by_search_and_packet_merging(self):
        terms = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon"
        write_page(self.vault, "career/partial.md", title=" ".join(terms.split()[:-1]))
        write_page(self.vault, "career/full.md", title="Complete lexical evidence", body=terms)
        direct = search_vault.search_vault(self.vault, terms, scope=["career"], limit=2)
        packet = prepare_context.prepare_context(self.vault, scope=["career"], anchors=[terms], result_limit=2)
        for results in (direct["results"], packet["matches"]):
            self.assertEqual([r["path"] for r in results], ["career/full.md", "career/partial.md"])
            self.assertEqual(results[0]["query_term_coverage"], 1.0)
            # The scalar is now deliberately secondary to coverage.
            self.assertLess(results[0]["rank_score"], results[1]["rank_score"])
        merged = prepare_context.prepare_context(
            self.vault, scope=["career"], anchors=[terms, "Complete lexical evidence"]
        )
        self.assertEqual(merged["matches"][0]["path"], "career/full.md")
        self.assertEqual(merged["matches"][0]["match_type"], "exact_title")
        self.assertEqual(len(merged["matches"][0]["matched_anchors"]), 2)

    def test_exact_identity_tiers_precede_lexical_scores(self):
        items = [
            {"match_type": kind, "matched_term_count": 1, "query_term_count": 1,
             "rank_score": score, "path": kind}
            for kind, score in (("lexical", 10**12), ("exact_alias", 3), ("exact_title", 2), ("exact_id", 1))
        ]
        self.assertEqual([i["match_type"] for i in sorted(items, key=search_vault.ranking_key)],
                         ["exact_id", "exact_title", "exact_alias", "lexical"])

    def replacement_packet(self, **kwargs):
        for i in range(3):
            write_page(self.vault, f"career/old-{i}.md", title=f"Uniqueanchor{i}",
                       status="superseded" if i == 0 else "active",
                       superseded_by="new.md" if i == 0 else None,
                       body="John Doe historical context.\n")
        write_page(self.vault, "career/new.md", title="Updated position", body="John Doe revised this position.\n")
        return prepare_context.prepare_context(
            self.vault, scope=["career"], anchors=[f"Uniqueanchor{i}" for i in range(3)],
            result_limit=3, include_evidence=True, **kwargs,
        )

    def test_successor_and_history_receive_slots_before_unrelated_matches(self):
        packet = self.replacement_packet()
        self.assertEqual(len(packet["evidence"]), 3)
        self.assertEqual([p["path"] for p in packet["evidence"][:2]], ["career/new.md", "career/old-0.md"])
        self.assertEqual([p["path"] for p in packet["matches"]],
                         ["career/old-1.md", "career/old-2.md", "career/old-0.md"])
        self.assertEqual(packet["evidence_omitted"],
                         [{"path": "career/old-2.md", "reason": "page limit exhausted"}])

    def test_successor_already_in_primary_matches_can_receive_evidence(self):
        self.replacement_packet()
        packet = prepare_context.prepare_context(
            self.vault, scope=["career"], anchors=["Uniqueanchor0", "Uniqueanchor1", "Uniqueanchor2", "Updated"],
            include_evidence=True, result_limit=4,
        )
        self.assertEqual(packet["matches"][3]["path"], "career/new.md")
        self.assertEqual(packet["related_replacements"], [])
        self.assertIn("career/new.md", [p["path"] for p in packet["evidence"]])

    def test_evidence_limits_are_explicit_and_zero_never_loads_evidence(self):
        packet = self.replacement_packet(evidence_page_limit=0)
        self.assertEqual(packet["evidence"], [])
        packet = self.replacement_packet(evidence_byte_limit=1)
        self.assertEqual(packet["evidence"], [])
        self.assertTrue(all(p["reason"] == "page too large" for p in packet["evidence_omitted"]))
        packet = self.replacement_packet()
        first = packet["evidence"][0]
        exact_budget = prepare_context._serialized_utf8_size([first])
        packet = self.replacement_packet(evidence_byte_limit=exact_budget)
        self.assertEqual(packet["evidence"], [first])
        self.assertLessEqual(prepare_context._serialized_utf8_size(packet["evidence"]), exact_budget)
        self.assertTrue(any(p["reason"] == "aggregate budget exhausted" for p in packet["evidence_omitted"]))

    def test_disabled_replacement_traversal_does_not_prioritize_successors(self):
        packet = self.replacement_packet(replacement_depth_limit=0)
        self.assertEqual(packet["related_replacements"], [])
        self.assertNotIn("career/new.md", [p["path"] for p in packet["evidence"]])

    def test_replacement_cycles_missing_targets_and_scope_stops_remain_visible(self):
        for successor, reason in (
            ("old-0.md", vault_utils.UNRESOLVED_CYCLE),
            ("missing.md", vault_utils.UNRESOLVED_MISSING_TARGET),
            ("../learning/outside.md", vault_utils.UNRESOLVED_OUT_OF_SCOPE),
        ):
            with self.subTest(reason=reason):
                self.replacement_packet()
                write_page(self.vault, "career/new.md", title="Replacement",
                           status="superseded", superseded_by=successor)
                before = tree_snapshot(self.vault)
                packet = prepare_context.prepare_context(
                    self.vault, scope=["career"], anchors=["Uniqueanchor0"],
                    include_evidence=True, evidence_page_limit=1,
                )
                self.assertEqual([p["path"] for p in packet["evidence"]], ["career/new.md"])
                self.assertEqual(packet["evidence"][0]["status"], "superseded")
                self.assertIn(reason, [r["reason"] for r in packet["unresolved_replacements"]])
                self.assertEqual(tree_snapshot(self.vault), before)

    def test_replacement_depth_stop_is_not_hidden_by_evidence_selection(self):
        self.replacement_packet()
        write_page(self.vault, "career/new.md", title="Intermediate", status="superseded", superseded_by="last.md")
        write_page(self.vault, "career/last.md", title="Current fictional record")
        packet = prepare_context.prepare_context(
            self.vault, scope=["career"], anchors=["Uniqueanchor0"],
            include_evidence=True, replacement_depth_limit=1,
        )
        self.assertNotIn("career/last.md", [p["path"] for p in packet["evidence"]])
        self.assertIn(vault_utils.UNRESOLVED_DEPTH_LIMIT, [r["reason"] for r in packet["unresolved_replacements"]])


if __name__ == "__main__":
    unittest.main()
