"""No GPU, model, network or third-party dependencies are used."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import preflight as pf

HERE = Path(__file__).resolve().parent


def fixture():
    return {
        'mode': 'memory_estimate', 'model': 'DeepSeek-R1-Distill-Qwen-14B',
        'parameter_count': 14_000_000_000, 'parameter_basis': 'nominal_unverified',
        'weight_bits': 16, 'weight_payload_bytes': None, 'tp': 2, 'weight_layout': 'sharded',
        'metadata_bytes': 0, 'replicated_bytes': 0,
        'extras_per_rank_bytes': 0, 'imbalance_percent': 0,
        'kv': {'kind': 'gqa', 'layers': 48, 'sequence_length': 4096, 'batch_size': 1,
               'kv_heads': 8, 'head_dim': 128, 'dtype_bytes': 2, 'allocation': 'sharded'},
        'hardware': {'gpu_count': 8, 'gpu_name': 'RTX A5000', 'sm': 86,
                     'nominal_bytes_per_gpu': pf.CAPACITY, 'free_bytes_per_rank': [23 * pf.GIB] * 2,
                     'memory_evidence': 'SYNTHETIC UNIT TEST ONLY',
                     'topology_evidence': 'SYNTHETIC UNIT TEST ONLY'}}


class PlannerTests(unittest.TestCase):
    def test_units_and_formula(self):
        r = pf.plan(fixture())
        self.assertEqual(pf.CAPACITY, 25_769_803_776)
        self.assertEqual(r['weight_lower_bound_bytes'], 28_000_000_000)
        self.assertEqual(r['kv_bytes_per_rank'], 402_653_184)
        self.assertEqual(r['status'], 'estimated_possible')
        self.assertFalse(r['runtime_admission'])
        self.assertFalse(r['gpu_tested'])

    def test_index_payload_selection(self):
        p = fixture()
        for payload in (29_540_067_328, 27_000_000_000):
            p['weight_payload_bytes'] = payload
            r = pf.plan(p)
            self.assertEqual(r['weight_lower_bound_bytes'], payload)
            self.assertEqual(r['nominal_parameter_bit_floor_bytes'], 28_000_000_000)
            self.assertEqual(r['weight_lower_bound_source'], 'caller_supplied_index_tensor_payload')
            self.assertEqual(r['weight_and_metadata_budget_per_rank_bytes'], pf.ceildiv(payload, 2))
        p['weight_payload_bytes'] = None
        self.assertEqual(pf.plan(p)['weight_lower_bound_source'], 'nominal_parameter_bits')

    def test_invalid_index_payload(self):
        for bad in (True, False, 0, -1, 2.5, float('nan'), float('inf'), '29540067328'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                p = fixture()
                p['weight_payload_bytes'] = bad
                pf.plan(p)

    def test_fp32_kv(self):
        p = fixture()
        before = pf.plan(p)['kv_bytes_per_rank']
        p['kv']['dtype_bytes'] = 4
        self.assertEqual(pf.plan(p)['kv_bytes_per_rank'], 2 * before)

    def test_replication(self):
        p = fixture()
        p['weight_layout'] = 'replicated'
        self.assertEqual(pf.plan(p)['status'], 'payload_exceeds_memory')
        p = fixture()
        p['kv']['kv_heads'] = 3
        with self.assertRaises(ValueError):
            pf.plan(p)
        p['kv']['allocation'] = 'replicated'
        self.assertEqual(pf.plan(p)['kv_heads_per_rank'], 3)
        self.assertEqual(pf.plan(p)['kv_bytes_per_rank'], 48 * 4096 * 2 * 3 * 128 * 2)

    def test_rank_not_total(self):
        p = fixture()
        p['hardware']['free_bytes_per_rank'] = [10 * pf.GIB, 24 * pf.GIB]
        r = pf.plan(p)
        self.assertGreater(sum(p['hardware']['free_bytes_per_rank']), r['planned_budget_all_selected_ranks_bytes'])
        self.assertEqual(r['status'], 'payload_exceeds_memory')

    def test_budget_excess_is_not_payload_impossibility(self):
        p = fixture()
        p['extras_per_rank_bytes'] = 20 * pf.GIB
        result = pf.plan(p)
        self.assertEqual(result['status'], 'budget_exceeds_memory')
        self.assertEqual(result['weight_payload_lower_bound_per_rank_bytes'], 14_000_000_000)
        self.assertGreater(result['planned_budget_per_rank_bytes'], pf.CAPACITY)
        p['extras_per_rank_bytes'] = 0
        p['imbalance_percent'] = 100
        self.assertEqual(pf.plan(p)['status'], 'budget_exceeds_memory')

    def test_unknown_topology_or_memory(self):
        for key in ('topology_evidence', 'memory_evidence'):
            p = fixture()
            p['hardware'][key] = None
            if key == 'memory_evidence':
                p['hardware']['free_bytes_per_rank'] = None
            self.assertEqual(pf.plan(p)['status'], 'unsupported_missing_evidence')

    def test_metadata_extras_imbalance(self):
        p = fixture()
        p.update(weight_bits=4, metadata_bytes=400, replicated_bytes=17, extras_per_rank_bytes=29, imbalance_percent=10)
        r = pf.plan(p)
        self.assertEqual(r['weight_lower_bound_bytes'], 7_000_000_000)
        budget = pf.ceildiv(pf.ceildiv(7_000_000_400, 2) * 110, 100)
        self.assertEqual(r['weight_and_metadata_budget_per_rank_bytes'], budget)
        self.assertEqual(r['planned_budget_per_rank_bytes'], budget + 46 + r['kv_bytes_per_rank'])

    def test_integer_ceil_no_float_rounding(self):
        p = fixture()
        p.update(parameter_count=9, weight_bits=3, metadata_bytes=1, imbalance_percent=1)
        r = pf.plan(p)
        self.assertEqual(r['weight_lower_bound_bytes'], 4)
        self.assertEqual(r['weight_and_metadata_budget_per_rank_bytes'], 4)
        self.assertEqual(pf.ceildiv(2**60 + 1, 8), 2**57 + 1)

    def test_full671b_even_ideal_four_bit_fails(self):
        p = fixture()
        p.update(parameter_count=671_000_000_000, weight_bits=4, tp=8, kv={'kind': 'mla_unmodeled'})
        p['hardware'].update(free_bytes_per_rank=None, memory_evidence=None, topology_evidence=None)
        r = pf.plan(p)
        self.assertEqual(r['weight_lower_bound_bytes'], 335_500_000_000)
        self.assertEqual(r['planned_budget_per_rank_bytes'], 41_937_500_000)
        self.assertEqual(r['status'], 'payload_exceeds_memory')
        self.assertIsNone(r['kv_bytes_per_rank'])

    def test_mla_never_uses_gqa(self):
        p = fixture()
        p['kv'] = {'kind': 'mla_unmodeled'}
        self.assertEqual(pf.plan(p)['status'], 'unsupported_missing_evidence')
        p['kv']['layers'] = 61
        with self.assertRaises(ValueError):
            pf.plan(p)

    def test_official_always_denied(self):
        p = fixture()
        p.update(mode='official_deepinfer', model='DeepSeek-V4.1-Flash', parameter_count=1)
        self.assertEqual(pf.plan(p)['status'], 'unsupported_native')
        for extra in ('force', 'runtime_admission', 'gpu_tested', 'execute', 'allow_sm86'):
            q = copy.deepcopy(p)
            q[extra] = True
            with self.assertRaises(ValueError):
                pf.plan(q)

    def test_bad_numeric_inputs(self):
        for key in ('parameter_count', 'weight_bits', 'tp'):
            for bad in (True, False, 0, -1, 1.5, float('nan'), float('inf'), '8', None):
                with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                    p = fixture()
                    p[key] = bad
                    pf.plan(p)
        for key in ('metadata_bytes', 'replicated_bytes', 'extras_per_rank_bytes', 'imbalance_percent'):
            for bad in (True, -1, 0.1, float('nan')):
                with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                    p = fixture()
                    p[key] = bad
                    pf.plan(p)
        for key in ('layers', 'sequence_length', 'batch_size', 'kv_heads', 'head_dim', 'dtype_bytes'):
            for bad in (True, 0, -1, float('inf')):
                with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                    p = fixture()
                    p['kv'][key] = bad
                    pf.plan(p)

    def test_hardware_validation(self):
        for key, bad in (('gpu_count', True), ('sm', 100), ('nominal_bytes_per_gpu', 24_000_000_000), ('free_bytes_per_rank', [pf.CAPACITY + 1] * 2), ('free_bytes_per_rank', [True] * 2), ('free_bytes_per_rank', [1]), ('topology_evidence', ''), ('memory_evidence', None)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                p = fixture()
                p['hardware'][key] = bad
                pf.plan(p)

    def test_cli_and_optimized_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'plan.json'
            for optimize in ([], ['-O']):
                for payload, code, status in ((json.dumps(fixture()), 0, 'estimated_possible'), ('{"tp": NaN}', 2, 'invalid_input'), ('{"tp": 2, "tp": 4}', 2, 'invalid_input')):
                    path.write_text(payload)
                    proc = subprocess.run([sys.executable] + optimize + [str(HERE / 'preflight.py'), str(path)], capture_output=True, text=True)
                    self.assertEqual(proc.returncode, code, proc.stderr)
                    self.assertEqual(json.loads(proc.stdout)['status'], status)
                p = fixture()
                p['mode'] = 'official_deepinfer'
                path.write_text(json.dumps(p))
                proc = subprocess.run([sys.executable] + optimize + [str(HERE / 'preflight.py'), str(path)], capture_output=True, text=True)
                self.assertEqual(proc.returncode, 1)
                self.assertEqual(json.loads(proc.stdout)['status'], 'unsupported_native')


if __name__ == '__main__':
    unittest.main()
