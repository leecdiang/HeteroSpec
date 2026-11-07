"""Synthetic CPU fixtures only. No native runtime, model weights or GPU forwards."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
import plan


def record(task, arm, session=0, round_=0, cost=10.0):
    return dict(task_id=task, arm=arm, session=session, round=round_, status='COMPLETE',
                whole_request_seconds=cost, cap=128, committed_ids=[11, 12, 99],
                runtime_eog_flags=[False, False, True], length=3, terminal_id=99,
                stop_reason='EOG', prompt_ids_sha256=hashlib.sha256(task.encode()).hexdigest())


def discovery(cost=5.0):
    tasks = [f'{d}/{i}' for d in ('MBPP', 'GSM8K') for i in range(6)]
    cid = 'Q8_0_native_greedy_k1'
    costs = {'R_32': 11, 'R_128': 10, 'R_512': 8, 'M_native_greedy': 7, cid: cost}
    return {'discovery_tasks': tasks, 'records': [record(t, a, s, cost=v)
            for t in tasks for a, v in costs.items() for s in (0, 1)],
            'candidates': [{'candidate_id': cid, 'matched_arm': 'M_native_greedy',
                            'gate_status': 'NATIVE_GATES_ADMITTED', 'peak_bytes': 1000}]}


def confirmation(sel):
    tasks = [f'{d}/{i}' for d in ('MBPP', 'GSM8K') for i in range(100000, 100012)]
    costs = {'R_stock': 10, 'R_prod': 8, 'M_match': 7, 'C_selected': 5}
    return {'confirmation_tasks': tasks, 'records': [record(t, a, s, n, v)
            for t in tasks for a, v in costs.items() for s in (0, 1) for n in range(4)],
            'candidate_id': sel['candidate_id'], 'ordinary_ub': sel['ordinary_ub'],
            'historical_and_rtx_reserved_ids': ['MBPP/999'],
            'history_audit_status': 'ACTUAL_FULL_HISTORY_AUDITED',
            'f0b_remote_status': 'ACTUAL_GIT_BLOBS_VERIFIED'}


class ContractTests(unittest.TestCase):
    def test_bounded_plan(self):
        p = plan.machine_plan()
        self.assertEqual(p['planned_engineering_max'], 485)
        self.assertEqual(len(p['candidates']), 12)
        self.assertEqual(p['formal_with_warmups'], 800)

    def test_asset_pins_are_complete_and_immutable_public_urls(self):
        pins = plan.read(plan.DOC / 'ASSETS.json')['models']
        self.assertEqual(len(pins), 6)
        for pin in pins.values():
            self.assertRegex(pin['sha256'], r'^[0-9a-f]{64}$')
            self.assertGreater(pin['bytes'], 0)
            self.assertFalse(pin['full_file_verified_on_b570_for_this_study'])
            if 'revision' in pin:
                self.assertRegex(pin['revision'], r'^[0-9a-f]{40}$')
                self.assertIn(pin['revision'], pin['url'])

    def test_fastest_ordinary_not_slow_stock(self):
        s = plan.select(discovery())
        self.assertEqual(s['ordinary_ub'], 512)
        self.assertEqual(s['status'], 'SELECTED_FOR_FRESH_CONFIRMATION')

    def test_beating_stock_but_losing_fast_ordinary_not_selected(self):
        s = plan.select(discovery(cost=8.5))
        self.assertEqual(s['status'], 'FEASIBLE_NO_PROMISING_GAIN')
        self.assertIsNone(s['qualified_formal_ratio'])

    def test_missing_candidate_record_no_selection(self):
        d = discovery()
        d['records'] = [r for r in d['records'] if not (r['arm'].endswith('_k1') and r['task_id'] == 'MBPP/0')]
        self.assertIsNone(plan.select(d)['candidate_id'])

    def test_optional_baseline_failure_visible(self):
        d = discovery()
        d['records'] = [r for r in d['records'] if r['arm'] != 'R_512']
        s = plan.select(d)
        self.assertEqual(s['ordinary_ub'], 128)
        self.assertEqual(s['baseline_observations'][-1]['status'], 'INELIGIBLE')

    def test_stock_instability_blocks(self):
        d = discovery()
        d['records'][2]['committed_ids'][0] = 13
        with self.assertRaises(ValueError):
            plan.select(d)

    def test_raw_eog_suffix_not_clipped(self):
        r = record('MBPP/0', 'R')
        r.update(committed_ids=[11, 99, 12], runtime_eog_flags=[False, True, False], terminal_id=12)
        with self.assertRaisesRegex(ValueError, 'SUFFIX'):
            plan.signature(r)

    def test_cap_overflow_and_invalid_timers_block(self):
        for change in ({'cap': 2}, {'whole_request_seconds': float('nan')}, {'status': 'FAILED'}):
            r = record('MBPP/0', 'R')
            r.update(change)
            with self.assertRaises(ValueError):
                plan.signature(r)

    def test_unlisted_candidate_and_wrong_matched_arm_block(self):
        for changes in ({'candidate_id': 'Q8_0_native_greedy_k4'}, {'matched_arm': 'R_128'}):
            d = discovery()
            d['candidates'][0].update(changes)
            with self.assertRaises(ValueError):
                plan.select(d)

    def test_full_fresh_confirmation(self):
        s = plan.select(discovery())
        result = plan.confirm(confirmation(s), s)
        self.assertEqual(result['formal_records'], 768)
        self.assertEqual(result['status'], 'POSITIVE_DESCRIPTIVE')
        self.assertAlmostEqual(result['comparisons']['R_prod/C_selected']['gm'], 1.6)
        self.assertIsNone(result['date_ci'])

    def test_exposure_overlap_discovery_or_rtx_rejected(self):
        s = plan.select(discovery())
        for source in ('discovery', 'rtx'):
            c = confirmation(s)
            if source == 'discovery':
                c['confirmation_tasks'][0] = s['discovery_tasks'][0]
            else:
                c['historical_and_rtx_reserved_ids'].append(c['confirmation_tasks'][0])
            with self.assertRaisesRegex(ValueError, 'OVERLAP'):
                plan.confirm(c, s)

    def test_bound_minimum_exposure_cannot_be_omitted(self):
        s = plan.select(discovery())
        c = confirmation(s)
        blocked = next(t for t in plan.read(plan.DOC / 'BASE_EXCLUSIONS.json')['excluded_ids'] if t.startswith('MBPP/'))
        c['confirmation_tasks'][0] = blocked
        c['historical_and_rtx_reserved_ids'] = []
        with self.assertRaisesRegex(ValueError, 'OVERLAP'):
            plan.confirm(c, s)

    def test_missing_duplicate_divergent_confirmation_rejected(self):
        s = plan.select(discovery())
        for kind in ('missing', 'duplicate', 'divergent'):
            c = confirmation(s)
            if kind == 'missing':
                c['records'].pop()
            elif kind == 'duplicate':
                c['records'].append(copy.deepcopy(c['records'][0]))
            else:
                c['records'][-1]['committed_ids'][0] = 42
            with self.assertRaises(ValueError):
                plan.confirm(c, s)

    def test_selection_change_and_remote_freeze_missing_rejected(self):
        s = plan.select(discovery())
        for change in ({'candidate_id': 'Q8_0_native_greedy_k3'}, {'ordinary_ub': 128},
                       {'f0b_remote_status': 'LOCAL_ONLY'}):
            c = confirmation(s)
            c.update(change)
            with self.assertRaises(ValueError):
                plan.confirm(c, s)

    def test_no_practical_gain_stays_visible(self):
        s = plan.select(discovery())
        c = confirmation(s)
        for r in c['records']:
            if r['arm'] == 'C_selected':
                r['whole_request_seconds'] = 9.0
        result = plan.confirm(c, s)
        self.assertEqual(result['status'], 'NO_PRACTICAL_POSITIVE_RESULT')
        self.assertLess(result['comparisons']['R_prod/C_selected']['gm'], 1)

    def test_evidence_hash_and_scope(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'proof.txt'
            p.write_bytes(b'CPU_SYNTHETIC_FIXTURE_ONLY')
            e = [{'role': 'native_source', 'path': p.name, 'bytes': p.stat().st_size, 'sha256': plan.sha(p)}]
            self.assertEqual(plan.bind_evidence(e, td), {'native_source'})
            p.write_bytes(b'changed')
            with self.assertRaises(ValueError):
                plan.bind_evidence(e, td)
            e[0]['path'] = '../outside'
            with self.assertRaises(ValueError):
                plan.bind_evidence(e, td)

    def test_missing_native_receipt_not_feasible(self):
        r = plan.host_check({}, '.')
        self.assertEqual(r['status'], 'BLOCKED_OR_UNKNOWN')
        self.assertIn('MISSING_LOADED_OR_PEAK_SAMPLE', r['reasons'])

    def test_external_memory_probe_partial_offload_insufficient_peak_block(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'CPU_SYNTHETIC.txt'
            p.write_bytes(b'NOT_A_GPU_EXPERIMENT')
            roles = ['native_source', 'binary', 'numeric_modules', 'load_log', 'vocab_dump',
                     'memory_trace', 'boundary_capture_reset_log']
            f = dict(evidence=[dict(role=r, path=p.name, bytes=p.stat().st_size, sha256=plan.sha(p)) for r in roles],
                     device_name='Intel Arc B570', backend='Vulkan', driver='SYNTHETIC',
                     source_review_status='ACTUAL_SOURCE_AND_LOGS_REVIEWED', family='Qwen',
                     context=1024, kv_type='F16', zero_load_forward_count=0, worker_pid=123)
            for name in ('full_native_vocab_equal', 'runtime_eog_flags_equal', 'native_compatibility_guard_enabled',
                         'no_shared_memory_spill', 'raw_commit_boundary_pass', 'capture_equivalence_pass', 'reset_pass'):
                f[name] = True
            pins = plan.read(plan.DOC / 'ASSETS.json')['models']
            for role in ('target', 'draft'):
                key = f'Qwen_{role}_Q8_0'
                f[role] = dict(asset_key=key, bytes=pins[key]['bytes'], sha256=pins[key]['sha256'],
                               full_file_verified=True, total_layers=25, gpu_layers=25, kv_gpu=True)
            f['memory_samples'] = [dict(point=x, scope='OWNED_MODEL_PROCESS', pid=123,
                device_name=f['device_name'], timestamp_utc='SYNTHETIC',
                heaps=[dict(dedicated_device_local=True, budget_bytes=10 * 2**30, usage_bytes=8 * 2**30)])
                for x in ('LOADED', 'ENGINEERING_PEAK')]
            self.assertFalse(plan.host_check(f, td)['reasons'])
            for change, expected in (
                    ('probe', 'MEMORY_PROBE_NOT_RESIDENT_WORKER'),
                    ('partial', 'DRAFT_PARTIAL_OFFLOAD_OR_UNKNOWN'),
                    ('peak', 'INSUFFICIENT_PEAK_HEADROOM'),
                    ('vocab', 'FULL_NATIVE_VOCAB_EQUAL'),
                    ('asset', 'TARGET_ASSET_UNVERIFIED')):
                b = copy.deepcopy(f)
                if change == 'probe':
                    b['memory_samples'][0]['pid'] = 999
                elif change == 'partial':
                    b['draft']['gpu_layers'] = 24
                elif change == 'peak':
                    b['memory_samples'][1]['heaps'][0]['usage_bytes'] = 10 * 2**30 - 100
                elif change == 'vocab':
                    b['full_native_vocab_equal'] = False
                else:
                    b['target']['sha256'] = 'wrong'
                self.assertIn(expected, plan.host_check(b, td)['reasons'])


if __name__ == '__main__':
    unittest.main()
