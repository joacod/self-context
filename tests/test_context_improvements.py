from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT / 'tests', ROOT / 'scripts', ROOT / '.agents/skills/self-context/scripts'):
    sys.path.insert(0, str(directory))

import evaluate_context
import ordinary_commit
import prepare_context
import search_vault
import sync_indexes
import vault_state
import vault_utils
from context_scenarios import build_context_scenarios
from synthetic_vault import tree_snapshot, write_page


class ContextImprovementTests(unittest.TestCase):
    def test_accent_fallback_preserves_strict_identity_and_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_context_scenarios(Path(temporary))
            write_page(vault, 'career/accent.md', title='Gestión', body='John Doe coordinated a project.')
            write_page(vault, 'career/plain.md', title='Gestion', body='John Doe coordinated another project.')
            before = tree_snapshot(vault)
            plain = search_vault.search_vault(vault, 'gestion', scope=['career'])['results']
            accented = search_vault.search_vault(vault, 'gestión', scope=['career'])['results']
            self.assertEqual(plain[0]['path'], 'career/plain.md')
            self.assertEqual(accented[0]['path'], 'career/accent.md')
            self.assertFalse(plain[0]['accent_folded'])
            self.assertTrue(next(r for r in plain if r['path'] == 'career/accent.md')['accent_folded'])
            self.assertEqual(before, tree_snapshot(vault))

    def test_bilingual_reformulation_stays_explicit_and_scoped(self):
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_context_scenarios(Path(temporary))
            first = search_vault.search_vault(vault, 'technical leadership', scope=['career'])['results']
            retry = search_vault.search_vault(vault, 'liderazgo tecnico', scope=['career'])['results']
            self.assertNotIn('career/leadership.md', [r['path'] for r in first])
            self.assertEqual(retry[0]['path'], 'career/leadership.md')
            self.assertTrue(retry[0]['accent_folded'])

    def test_snapshot_reuse_matches_fresh_hash_and_active_validation_stays_fresh(self):
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_context_scenarios(Path(temporary))
            captured = vault_state.canonical_bytes(vault)
            self.assertEqual(vault_state.snapshot_from_bytes(captured), vault_utils.snapshot_id(vault))
            proposal = {'expected_snapshot': vault_utils.snapshot_id(vault),
                        'writes': {'career/leadership.md': (vault / 'career/leadership.md').read_text() + '\nAdditional fictional evidence.\n'},
                        'log': {'operation': 'ingest', 'summary': 'Extend fictional evidence', 'paths': ['career/leadership.md']}}
            with mock.patch.object(sync_indexes, 'synchronize', wraps=sync_indexes.synchronize) as synchronize:
                result = ordinary_commit.commit_mutation(vault, proposal)
            self.assertEqual(result['status'], 'success', result)
            calls = synchronize.call_args_list
            self.assertEqual(len(calls), 3)
            self.assertIs(calls[0].kwargs['records'], calls[1].kwargs['records'])
            self.assertNotIn('records', calls[2].kwargs)
            self.assertEqual(Path(calls[2].args[0]), vault)

    def test_packet_cap_preserves_complete_evidence_or_blocks_safely(self):
        with tempfile.TemporaryDirectory() as temporary:
            vault = build_context_scenarios(Path(temporary))
            before = tree_snapshot(vault)
            for limit in (1024, 4096, 32768):
                packet = prepare_context.prepare_context(vault, scope=['career'], anchors=['liderazgo tecnico'],
                    include_evidence=True, for_update=True, packet_byte_limit=limit)
                self.assertLessEqual(len(json.dumps(packet, ensure_ascii=False, sort_keys=True).encode()), limit)
                for evidence in packet['evidence']:
                    self.assertEqual(evidence['content'], (vault / evidence['path']).read_text())
                if packet['runtime']['state'] == 'packet-budget-exceeded':
                    self.assertFalse(packet['controls']['mutation_ready'])
                    self.assertIsNone(packet['controls']['expected_snapshot'])
            self.assertEqual(before, tree_snapshot(vault))
            with self.assertRaises(ValueError):
                prepare_context.prepare_context(vault, packet_byte_limit=100)

    def test_required_qualifications_cannot_be_silently_trimmed(self):
        packet = {'runtime': {'state': 'current'}, 'controls': {}, 'navigation': [],
                  'findings': [{'message': 'qualification' * 1000}], 'evidence': [], 'matches': [],
                  'unresolved_replacements': [{'path': 'career/missing.md'}]}
        bounded = prepare_context._bound_packet(packet, 1024)
        self.assertEqual(bounded['runtime']['state'], 'packet-budget-exceeded')
        self.assertFalse(bounded['controls']['mutation_ready'])

    def test_evaluation_refuses_existing_root_and_reports_unintended_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / 'run'
            evaluate_context.prepare(destination)
            with self.assertRaises(FileExistsError):
                evaluate_context.prepare(destination)
            report = evaluate_context.check(destination)
            self.assertFalse(any(row['responded'] for row in report['outcomes']))
            (destination / 'exact/vault/core/unexpected.md').write_text('unexpected')
            report = evaluate_context.check(destination)
            row = next(row for row in report['outcomes'] if row['id'] == 'exact')
            self.assertFalse(row['mechanical_ok'])
            self.assertEqual(row['unexpected_writes'], ['core/unexpected.md'])


if __name__ == '__main__':
    unittest.main()
