"""CPU-only synthetic tests of architecture export boundaries; no native evidence.
Fixtures intentionally assert NATIVE to exercise admission paths. Temporary raw files
are explicitly synthetic: passing hashes is NOT proof of real native execution.
"""
import copy
import tempfile
import unittest
from pathlib import Path
import architecture as ar
import protocol as p
from test_toolkit import pilot, confirm, record, endpoint, HASH


class ArchitectureBoundary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.plan = pilot()
        self.slot = next(s for s in self.plan['slots'] if s['arm'] == 'C_R_QB' and s['mode'] == 'counts')
        self.rec = self.fixture(self.slot)
        rs = next(s for s in self.plan['slots'] if s['arm'] == 'R'
                  and s['task'] == self.slot['task'] and s['session'] == self.slot['session'])
        self.ref = self.fixture(rs)

    def fixture(self, slot):
        rec = record(slot)
        rec['evidence_origin'] = 'NATIVE'  # Mocked claim, never actual experiment evidence.
        for role in ('request', 'result', 'identity', 'lifecycle'):
            path = self.root / (slot['slot'] + '.' + role)
            path.write_bytes(('SYNTHETIC_TEST_ONLY:' + slot['slot'] + ':' + role).encode())
            rec['raw_artifacts'].append({'role': role, 'path': path.name,
                                         'bytes': path.stat().st_size, 'sha256': p.file_sha(path)})
        return rec

    def export(self, rec=None, **kwargs):
        args = dict(plan=self.plan, frozen_runtime_sha256=HASH, raw_root=self.root)
        args.update(kwargs)
        return ar.architecture_record(self.rec if rec is None else rec, **args)

    def test_01_missing_context_rejected(self):
        with self.assertRaises(ValueError):
            ar.architecture_record(self.rec)

    def test_02_digest_mismatch_rejected(self):
        self.rec['normalized_sent_request']['prompt_ids'][0] += 1
        with self.assertRaises(ValueError):
            self.export()

    def test_03_external_runtime_pin_rejected(self):
        with self.assertRaises(ValueError):
            self.export(frozen_runtime_sha256='b' * 64)

    def test_04_counts_observer_contamination_rejected(self):
        for flag in self.rec['observation']:
            with self.subTest(flag=flag):
                rec = copy.deepcopy(self.rec); rec['observation'][flag] = True
                with self.assertRaises(ValueError): self.export(rec)

    def test_05_invalid_timer_rejected(self):
        self.rec['timer_contract'] = 'CPU_ENQUEUE_ONLY'
        with self.assertRaises(ValueError): self.export()

    def test_06_invalid_wall_rejected(self):
        for wall in (float('nan'), float('inf'), -1, 0, True):
            with self.subTest(wall=wall):
                rec = copy.deepcopy(self.rec); rec['request_wall_ms'] = wall
                with self.assertRaises(ValueError): self.export(rec)

    def test_07_missing_raw_rejected(self):
        self.rec['raw_artifacts'] = []
        with self.assertRaises(ValueError): self.export()

    def test_08_corrupt_raw_rejected(self):
        (self.root / self.rec['raw_artifacts'][0]['path']).write_bytes(b'CORRUPTED')
        with self.assertRaises(ValueError): self.export()

    def test_09_unknown_reference_is_not_pass(self):
        out = self.export()
        self.assertEqual(out['qualification']['paired_original_reference_endpoint'], 'NOT_CHECKED')
        self.assertIsNone(out['request_time']['panel_qualified_cost'])
        self.assertFalse(out['source']['independent_raw_semantics_verified'])
        self.assertFalse(out['source']['execution_f0_authenticated_by_this_exporter'])

    def test_10_pair_match_is_not_panel_or_hardware_pass(self):
        out = self.export(reference_record=self.ref)
        self.assertEqual(out['qualification']['paired_original_reference_endpoint'], 'MATCH')
        self.assertEqual(out['qualification']['panel_qualification'], 'NOT_ESTABLISHED_BY_SINGLE_RECORD')
        self.assertIsNone(out['request_time']['hardware_speedup'])
        self.assertEqual(out['hardware_stage1']['admission'], 'NOT_DECIDED_BY_EXPORTER')

    def test_11_counterexample_keeps_work_and_diagnostic_time(self):
        self.rec['endpoint'] = endpoint(55)
        out = self.export(reference_record=self.ref)
        self.assertEqual(out['qualification']['paired_original_reference_endpoint'], 'MISMATCH')
        self.assertEqual(out['request_time']['ms'], self.rec['request_wall_ms'])
        self.assertIsNone(out['request_time']['panel_qualified_cost'])
        self.assertGreater(out['measured_native_work']['target_continuation_rows'], 0)

    def test_12_wrong_task_reference_rejected(self):
        s = next(s for s in self.plan['slots'] if s['arm'] == 'R' and s['task'] != self.slot['task'])
        with self.assertRaises(ValueError): self.export(reference_record=self.fixture(s))

    def test_13_wrong_session_reference_rejected(self):
        s = next(s for s in self.plan['slots'] if s['arm'] == 'R' and s['task'] == self.slot['task'] and s['session'] == 1)
        with self.assertRaises(ValueError): self.export(reference_record=self.fixture(s))

    def test_14_shadow_is_not_original_reference(self):
        s = next(s for s in self.plan['slots'] if s['arm'] == 'R_SHADOW' and s['task'] == self.slot['task'] and s['mode'] == 'counts')
        with self.assertRaises(ValueError): self.export(reference_record=self.fixture(s))

    def test_15_diagnostic_not_paid(self):
        s = next(s for s in self.plan['slots'] if s['arm'] == 'C_R_QB' and s['task'] == self.slot['task'] and s['mode'] == 'diagnostic')
        out = self.export(self.fixture(s), reference_record=self.ref)
        self.assertEqual(out['request_time']['classification'], 'DIAGNOSTIC_ONLY')
        self.assertFalse(out['request_time']['clean_counts_nonwarmup'])

    def test_16_warmup_not_paid(self):
        plan = confirm(); s = next(s for s in plan['slots'] if s['warmup'])
        out = self.export(self.fixture(s), plan=plan)
        self.assertEqual(out['request_time']['classification'], 'WARMUP_EXCLUDED')
        self.assertFalse(out['request_time']['clean_counts_nonwarmup'])

    def test_17_histogram_does_not_invent_timeline_or_hardware(self):
        self.rec['work']['DRAM_bytes'] = 123  # Unknown extension must not become measured work.
        out = self.export()
        self.assertEqual(out['geometry']['declared_maximum_query_rows'], 2)
        for name in ('actual_caller_query_rows', 'verify_transaction_width_witness',
                     'ordered_transaction_trace', 'physical_compute_resource_width', 'operator_key_extent'):
            self.assertIsNone(out['geometry'][name])
        self.assertIsNone(out['geometry']['observed_prefill_micrograph_widths'])
        self.assertIsNone(out['unmeasured']['DRAM_bytes'])
        self.assertNotIn('DRAM_bytes', out['measured_native_work'])

    def test_18_export_is_detached(self):
        out = self.export(reference_record=self.ref)
        self.rec['normalized_sent_request']['recipe']['k'] = 99
        self.ref['raw_artifacts'].clear()
        self.assertEqual(out['recipe']['k'], 1)
        self.assertEqual(len(out['qualification']['paired_reference']['raw_artifacts']), 4)

    def test_19_invalid_plan_rejected(self):
        self.plan['slots'].pop()
        with self.assertRaises(ValueError): self.export()

    def test_20_incomplete_record_rejected(self):
        self.rec['status'] = 'FAILED'
        with self.assertRaises(ValueError): self.export()

    def test_21_synthetic_reference_rejected(self):
        self.ref['evidence_origin'] = 'SYNTHETIC_TEST_ONLY'
        with self.assertRaises(ValueError): self.export(reference_record=self.ref)

    def test_22_reuse_does_not_claim_qfold_gain(self):
        self.assertEqual(ar.reuse_opportunity(2, 4096, 2)['candidate_vs_strong_shared_baseline_ratio'], 1)
        q = 2**60 + 1
        self.assertEqual(ar.reuse_opportunity(q, 1, 2)['context_group_shared_fetch_bytes'], (q + 1)//2)
        with self.assertRaises(ValueError): ar.reuse_opportunity(True, 4096, 2)

    def test_23_amdahl_boundaries(self):
        self.assertEqual(ar.amdahl_sensitivity(0., 2.)['whole_request_speedup_if_assumptions_hold'], 1.)
        self.assertLess(ar.amdahl_sensitivity(.2, 2., .2)['whole_request_speedup_if_assumptions_hold'], 1.)
        for args in ((True, 2.), (.2, 0.), (.2, float('inf')), (1., 1e-320)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError): ar.amdahl_sensitivity(*args)

    def test_24_raw_path_escape_rejected(self):
        self.rec['raw_artifacts'][0]['path'] = '../outside'
        with self.assertRaises(ValueError): self.export()


if __name__ == '__main__':
    unittest.main(verbosity=2)
