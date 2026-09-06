from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.agents/skills/self-context/scripts'))
import prepare_context
import search_vault
import vault_utils
from synthetic_vault import build_synthetic_vault, write_page


@contextmanager
def observe_work(vault: Path):
    """Observe actual page reads and directory scans, not filtered outputs."""
    vault = vault.resolve()
    reads: Counter[str] = Counter()
    scans: Counter[str] = Counter()
    read_bytes = Path.read_bytes
    scandir = os.scandir

    def read(path):
        resolved = path.resolve()
        if resolved.is_relative_to(vault):
            reads[resolved.relative_to(vault).as_posix()] += 1
        return read_bytes(path)

    def scan(path):
        path = Path(path).resolve()
        if path.is_relative_to(vault):
            scans[path.relative_to(vault).as_posix()] += 1
        return scandir(path)

    with mock.patch.object(Path, 'read_bytes', read), mock.patch.object(os, 'scandir', scan):
        yield reads, scans


class RetrievalScopeTests(unittest.TestCase):
    def test_unrelated_growth_does_not_add_reads_or_branch_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            previous_size = 0
            baseline_work = None
            for size in (0, 100, 1000):
                for number in range(previous_size, size):
                    write_page(vault, f'learning/unrelated/{number}.md', title='Unrelated learning')
                previous_size = size
                with observe_work(vault) as work:
                    report = search_vault.search_vault(vault, 'Harbor Launch', scope=['career'])
                self.assertEqual([item['path'] for item in report['results']], [
                    'career/harbor-launch.md', 'career/superseded-launch.md', 'career/archived-role.md',
                ])
                reads, scans = work
                self.assertEqual(reads, Counter({
                    'career/archived-role.md': 1, 'career/harbor-launch.md': 1,
                    'career/superseded-launch.md': 1,
                }))
                self.assertEqual(scans, Counter({'.': 1, 'career': 1}))
                if baseline_work is not None:
                    self.assertEqual(work, baseline_work)
                baseline_work = work

    def test_nested_file_overlapping_and_vertical_scopes_prune_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            for relative in ('career/nested/a.md', 'career/nested/b.md', 'career/other/c.md'):
                write_page(vault, relative, title='Deterministic Tie', description='Identical match', body='Identical body')
            cases = [
                (['career/nested'], None, ['career/nested/a.md', 'career/nested/b.md']),
                (['career/nested/a.md'], None, ['career/nested/a.md']),
                (['career/nested/b.md', 'career/nested', 'career/nested/a.md'], 'career', ['career/nested/a.md', 'career/nested/b.md']),
                (['career/nested', 'learning'], 'career', ['career/nested/a.md', 'career/nested/b.md']),
                (['career/nested'], 'learning', []),
                (['career'], 'unknown-vertical', []),
                (['career/absent.md'], None, []),
            ]
            for scopes, vertical, expected in cases:
                with self.subTest(scopes=scopes, vertical=vertical), observe_work(vault) as (reads, scans):
                    report = search_vault.search_vault(vault, 'Deterministic Tie', scope=scopes, vertical=vertical)
                self.assertEqual([item['path'] for item in report['results']], expected)
                self.assertEqual(reads, Counter({path: 1 for path in expected}))
                self.assertNotIn('career/other', scans)
                self.assertNotIn('learning', scans)
                for item in report['results']:
                    self.assertEqual(item['match_type'], 'exact_title')
                    self.assertEqual(item['rank_score'], 900052000)
                    self.assertEqual(item['vertical'], 'career')
            with observe_work(vault) as (reads, scans):
                report = search_vault.search_vault(vault, 'Harbor Launch', vertical='career')
            self.assertEqual(len(reads), 6)
            self.assertNotIn('learning', scans)
            self.assertEqual(report['results'][0]['path'], 'career/harbor-launch.md')

    def test_multiple_anchors_reuse_selected_pages_and_cross_scope_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            with observe_work(vault) as (reads, scans):
                packet = prepare_context.prepare_context(
                    vault, scope=['career'], anchors=['Harbor Launch', 'harbor delivery'],
                    result_limit=3, recent_limit=0, expand_linked_sources=True,
                )
            self.assertEqual(reads, Counter({
                'career/archived-role.md': 1, 'career/harbor-launch.md': 1,
                'career/superseded-launch.md': 1, 'sources/harbor-notes.md': 1,
                'sources/old-role-notes.md': 1,
            }))
            self.assertNotIn('sources', scans)
            self.assertNotIn('learning', scans)
            self.assertEqual(packet['matches'][0]['matched_anchors'], ['Harbor Launch', 'harbor delivery'])
            source = packet['linked_sources'][0]
            self.assertEqual(source['path'], 'sources/harbor-notes.md')
            self.assertEqual(source['linked_from'], 'career/harbor-launch.md')
            self.assertEqual(source['match_type'], 'linked_source')
            self.assertEqual(source['rank_score'], -1)

    def test_provenance_filters_unsafe_missing_malformed_and_non_source_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            for relative in ('sources/good.MD', 'sources/late.md', '.obsidian/hidden.md', 'backups/hidden.md', 'review/deep-reviews/report.md'):
                write_page(vault, relative, title='Source', page_type='source', assertion_kind='source_record')
            (vault / 'sources/malformed.md').write_text('No frontmatter\n')
            (vault / 'sources/file-link.md').symlink_to(vault / 'sources/late.md')
            (vault / 'source-alias').symlink_to(vault / 'sources', target_is_directory=True)
            outside = Path(temporary) / 'outside.md'
            outside.write_text('Must never be read')
            (vault / 'sources/outside-link.md').symlink_to(outside)
            links = [
                '../sources/missing.md', '../sources/malformed.md', '../core/decision-trail.md',
                '../sources/index.md', '../SCHEMA.md', '../log.md',
                '../review/deep-reviews/report.md', '../.obsidian/hidden.md', '../backups/hidden.md',
                '../sources/file-link.md', '../source-alias/late.md', '../sources/outside-link.md',
                '../source-alias/../sources/late.md', '../../outside.md',
                'https://example.com/source', '../sources/good%2EMD#evidence',
                '../sources/good.MD', '../sources/late.md',
            ]
            write_page(vault, 'career/anchor.md', title='Exact Anchor', sources=links)
            with observe_work(vault) as (reads, scans):
                report = search_vault.search_vault(
                    vault, 'Exact Anchor', scope=['career/anchor.md'],
                    expand_linked_sources=True, limit=2,
                )
            self.assertEqual([item['path'] for item in report['results']], ['career/anchor.md', 'sources/good.MD'])
            self.assertEqual(reads, Counter({
                'career/anchor.md': 1, 'sources/malformed.md': 1,
                'core/decision-trail.md': 1, 'sources/good.MD': 1,
            }))
            self.assertEqual(scans, Counter({'.': 1, 'career': 1}))
            # Larger budgets retain link order and deduplicate a repeated target.
            report = search_vault.search_vault(vault, 'Exact Anchor', scope=['career/anchor.md'], expand_linked_sources=True, limit=10)
            self.assertEqual([item['path'] for item in report['results']], ['career/anchor.md', 'sources/good.MD', 'sources/late.md'])

    def test_sources_are_only_loaded_for_selected_results_and_available_slots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            for limit, expansion in ((1, True), (10, False)):
                with observe_work(vault) as (reads, _):
                    search_vault.search_vault(vault, 'Harbor Launch', scope=['career'], limit=limit, expand_linked_sources=expansion)
                self.assertEqual(set(reads), {'career/archived-role.md', 'career/harbor-launch.md', 'career/superseded-launch.md'})
            with observe_work(vault) as (reads, _):
                report = search_vault.search_vault(vault, 'Harbor Launch', scope=['career'], limit=2, expand_linked_sources=True)
            self.assertEqual([item['path'] for item in report['results']], ['career/harbor-launch.md', 'sources/harbor-notes.md'])
            self.assertNotIn('sources/old-role-notes.md', reads)

    def test_control_reports_and_symlinks_are_excluded_before_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            write_page(vault, 'review/deep-reviews/existing-review.md', title='Event Model')
            (vault / 'career/link.md').symlink_to(vault / 'learning/event-model.md')
            (vault / 'career/linked-dir').symlink_to(vault / 'learning', target_is_directory=True)
            with observe_work(vault) as (reads, scans):
                report = search_vault.search_vault(vault, 'Event Model', scope=['career/link.md', 'career/linked-dir', 'review', 'SCHEMA.md', 'log.md'])
            self.assertEqual(report['results'], [])
            self.assertEqual(set(reads), {'review/maintenance-candidate.md'})
            self.assertNotIn('career/linked-dir', scans)
            with observe_work(vault) as (reads, _):
                records = vault_utils.durable_page_records(vault, include_reports=True)
            self.assertIn('review/deep-reviews/existing-review.md', reads)
            self.assertTrue(any(record['is_deep_report'] for record in records))

    def test_zero_limits_keep_runtime_and_orientation_without_candidate_work(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            with (
                observe_work(vault) as (reads, _),
                mock.patch.object(search_vault, '_score_record', side_effect=AssertionError('must not score')),
            ):
                report = search_vault.search_vault(vault, 'Harbor Launch', scope=['career'], limit=0, expand_linked_sources=True)
                packet = prepare_context.prepare_context(vault, scope=['career'], anchors=['Harbor Launch'], result_limit=0, expand_linked_sources=True)
            self.assertEqual(reads, {})
            self.assertEqual(report['results'], [])
            self.assertTrue(report['runtime_compatibility']['ok'])
            self.assertEqual(packet['matches'], [])
            self.assertEqual(packet['linked_sources'], [])
            self.assertEqual({item['path'] for item in packet['navigation']}, {'index.md', 'career/index.md'})
            (vault / 'SCHEMA.md').write_text('schema_version: 99.0\n')
            blocked = search_vault.search_vault(vault, 'Harbor', scope=['career'], limit=0)
            self.assertTrue(blocked['findings'])
            self.assertFalse(blocked['runtime_compatibility']['ok'])

    def test_only_selected_results_are_rendered_and_calls_observe_fresh_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_synthetic_vault(Path(temporary))
            with mock.patch.object(search_vault, '_render_result', wraps=search_vault._render_result) as render:
                report = search_vault.search_vault(vault, 'Harbor Launch', scope=['career'], limit=1)
            self.assertEqual(render.call_count, 1)
            self.assertEqual(report['results'][0]['path'], 'career/harbor-launch.md')
            write_page(vault, 'career/harbor-launch.md', title='Fresh Anchor', sources=['../sources/harbor-notes.md'])
            write_page(vault, 'sources/harbor-notes.md', title='Fresh Source', page_type='source')
            report = search_vault.search_vault(vault, 'Fresh Anchor', scope=['career'], limit=2, expand_linked_sources=True)
            self.assertEqual([item['title'] for item in report['results']], ['Fresh Anchor', 'Fresh Source'])
            (vault / 'sources/harbor-notes.md').unlink()
            (vault / 'career/harbor-launch.md').rename(vault / 'career/moved.md')
            report = search_vault.search_vault(vault, 'Fresh Anchor', scope=['career'], limit=2, expand_linked_sources=True)
            self.assertEqual([item['path'] for item in report['results']], ['career/moved.md'])


if __name__ == '__main__':
    unittest.main()
